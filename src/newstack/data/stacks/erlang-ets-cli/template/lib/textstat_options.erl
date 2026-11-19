%% A hand-written argv parser: no getopt, no dependencies.
-module(textstat_options).
-export([parse/1, usage/1, version/0]).
-export_type([parsed/0]).

-type status() :: ok | help | version | usage_error.
-type parsed() :: #{status := status(),
                    message := string(),
                    figures := [l | w | c],
                    files := [string()]}.

-spec version() -> string().
version() -> "0.1.0".

-spec usage(string()) -> string().
usage(Program) ->
    lists:flatten(
      ["usage: ", Program, " [-l] [-w] [-c] [FILE ...]\n",
       "\n",
       "Count lines, words and bytes.  Each figure is printed only when its flag\n",
       "is given; with no flags all three are.  With no FILE, or when FILE is -,\n",
       "read standard input.\n",
       "\n",
       "  -l, --lines    lines\n",
       "  -w, --words    words\n",
       "  -c, --bytes    bytes\n",
       "  -h, --help     show this message\n",
       "  -V, --version  show the version\n"]).

-spec parse([string()]) -> parsed().
parse(Args) ->
    finish(walk(Args, #{status => ok, message => "", figures => [], files => [], only => false})).

%% Once help, --version or a bad option has been seen, the rest is noise.
walk([], S) ->
    S;
walk([_ | _Rest], #{status := Status} = S) when Status =/= ok ->
    S;
walk(["--" | Rest], #{only := false} = S) ->
    walk(Rest, S#{only := true});
walk(["-" | Rest], #{only := false} = S) ->
    walk(Rest, add_file("-", S));
walk(["--" ++ Name | Rest], #{only := false} = S) ->
    case long_flag(Name) of
        help -> S#{status := help};
        version -> S#{status := version};
        {figure, Figure} -> walk(Rest, add_figure(Figure, S));
        unknown -> S#{status := usage_error, message := "unknown option: --" ++ Name}
    end;
walk(["-h" | Rest], #{only := false} = S) ->
    walk(Rest, S#{status := help});
walk(["-V" | Rest], #{only := false} = S) ->
    walk(Rest, S#{status := version});
walk([[$- | Letters] | Rest], #{only := false} = S) ->
    walk_cluster(Letters, Rest, S);
walk([File | Rest], S) ->
    walk(Rest, add_file(File, S)).

%% "-lw" is two flags in one argument; a bad letter stops the whole parse.
walk_cluster([], Rest, S) ->
    walk(Rest, S);
walk_cluster([Letter | Letters], Rest, S) ->
    case figure(Letter) of
        {ok, Figure} -> walk_cluster(Letters, Rest, add_figure(Figure, S));
        error -> S#{status := usage_error, message := "unknown option: -" ++ [Letter]}
    end.

figure($l) -> {ok, l};
figure($w) -> {ok, w};
figure($c) -> {ok, c};
figure(_) -> error.

long_flag("lines") -> {figure, l};
long_flag("words") -> {figure, w};
long_flag("bytes") -> {figure, c};
long_flag("help") -> help;
long_flag("version") -> version;
long_flag(_) -> unknown.

add_file(File, #{files := Files} = S) ->
    S#{files := Files ++ [File]}.

add_figure(Figure, #{figures := Figures} = S) ->
    case lists:member(Figure, Figures) of
        true -> S;
        false -> S#{figures := Figures ++ [Figure]}
    end.

finish(#{status := ok, figures := []} = S) ->
    S#{figures := [l, w, c]};
finish(S) ->
    S.
