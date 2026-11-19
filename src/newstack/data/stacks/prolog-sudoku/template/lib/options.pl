%% Hand-written option parser; all arguments are strings.
:- module(options, [parse_options/2, status_ok/1, status_help/1, status_usage/1]).

status_ok(0).
status_help(1).
status_usage(2).

parse_options(Args, Opts) :-
    Opts0 = options{status: 0, message: "", path: "", limit: 1},
    parse_args(Args, Opts0, Opts1),
    (   Opts1.status =:= 0, Opts1.path == ""
    ->  put_dict(status, Opts1, 2, T1), put_dict(message, T1, "expected a grid file", Opts)
    ;   Opts = Opts1
    ),
    !.

parse_args([], Opts, Opts).
parse_args(["-h"|_], Opts, Result) :- !, put_dict(status, Opts, 1, Result).
parse_args(["--help"|_], Opts, Result) :- !, put_dict(status, Opts, 1, Result).
parse_args(["--limit", N|Rest], Opts, Result) :-
    !,
    catch(number_string(Limit, N), _, fail),
    Limit >= 1,
    put_dict(limit, Opts, Limit, Opts1),
    parse_args(Rest, Opts1, Result).
parse_args([Path|Rest], Opts, Result) :-
    \+ sub_string(Path, 0, 1, _, "-"), !,
    put_dict(path, Opts, Path, Opts1),
    parse_args(Rest, Opts1, Result).
parse_args([Arg|_], Opts, Result) :-
    format(string(Msg), "unexpected argument: ~w", [Arg]),
    put_dict(status, Opts, 2, T1), put_dict(message, T1, Msg, Result).
