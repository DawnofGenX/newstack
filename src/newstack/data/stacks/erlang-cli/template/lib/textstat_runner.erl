%% The process-facing layer: it decides what to print and which code to exit.
%%
%% The IO boundary is a map of funs, so the tests can hand it a fake filesystem
%% and two real temporary files instead of a process.
-module(textstat_runner).
-export([run/2, program/0, format_row/3]).
-export_type([io_map/0]).

-type io_map() :: #{read_file := fun((string()) -> {ok, binary()} | {error, term()}),
                    read_stdin := fun(() -> binary()),
                    out := fun((unicode:chardata()) -> ok),
                    err := fun((unicode:chardata()) -> ok)}.

-spec program() -> string().
program() -> "{{ npm_name }}".

%% @doc 0 success, 1 a file could not be read, 2 a usage error.
-spec run([string()], io_map()) -> 0 | 1 | 2.
run(Args, Io) ->
    Parsed = textstat_options:parse(Args),
    case maps:get(status, Parsed) of
        help ->
            say(out, Io, textstat_options:usage(program())),
            0;
        version ->
            say(out, Io, [program(), " ", textstat_options:version(), "\n"]),
            0;
        usage_error ->
            say(err, Io, [program(), ": ", maps:get(message, Parsed), "\n",
                          "Try '", program(), " --help' for more information.\n"]),
            2;
        ok ->
            report(maps:get(figures, Parsed), operands(maps:get(files, Parsed)), Io)
    end.

operands([]) -> ["-"];
operands(Files) -> Files.

report(Figures, Files, Io) ->
    ReadFile = maps:get(read_file, Io),
    {Rows, Total, Failures} =
        lists:foldl(fun(Path, Acc) -> read_row(Path, ReadFile, Acc, Io) end,
                    {[], {0, 0, 0}, 0}, Files),
    Printed = case length(Files) > 1 of
                  true -> Rows ++ [{"total", Total}];
                  false -> Rows
              end,
    Width = width(Figures, Printed),
    lists:foreach(fun({Label, Counts}) ->
                          say(out, Io, [format_row(textstat_counts:columns(Figures, Counts),
                                                   Label, Width), "\n"])
                  end, Printed),
    case Failures of
        0 -> 0;
        _ -> 1
    end.

read_row(Path, ReadFile, {Rows, Total, Failures}, Io) ->
    case read(Path, ReadFile, Io) of
        {ok, Data} ->
            Counts = textstat_counts:of_binary(Data),
            {Rows ++ [{Path, Counts}], textstat_counts:add(Total, Counts), Failures};
        error ->
            {Rows, Total, Failures + 1}
    end.

read("-", _ReadFile, Io) ->
    {ok, (maps:get(read_stdin, Io))()};
read(Path, ReadFile, Io) ->
    case ReadFile(Path) of
        {ok, Data} ->
            {ok, Data};
        {error, _} ->
            say(err, Io, ["error: cannot open '", Path, "'\n"]),
            error
    end.

%% wc right-aligns every figure in one shared width, per printed row.
width(Figures, Rows) ->
    Digits = [[length(integer_to_list(Value)) || Value <- textstat_counts:columns(Figures, Counts)]
              || {_Label, Counts} <- Rows],
    lists:max([1 | lists:append(Digits)]).

-spec format_row([non_neg_integer()], string(), pos_integer()) -> string().
format_row(Values, Label, Width) ->
    Cells = [pad(Value, Width) || Value <- Values],
    lists:flatten(lists:join(" ", Cells) ++ " " ++ Label).

pad(Value, Width) ->
    Digits = integer_to_list(Value),
    lists:duplicate(max(0, Width - length(Digits)), $\s) ++ Digits.

say(Which, Io, Data) ->
    (maps:get(Which, Io))(Data).
