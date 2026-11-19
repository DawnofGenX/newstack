:- module(harness, [reset/0, check/2, check_eq/3, report/0, capture/4, out_text/1, err_text/1]).

reset :- nb_setval(passed, 0), nb_setval(failed, 0), nb_setval(out, ""), nb_setval(err, "").
bump(K) :- ( nb_current(K, V) -> N is V + 1 ; N = 1 ), nb_setval(K, N).
check(Name, Goal) :- ( catch(call(Goal), _, fail) -> bump(passed) ; format("FAIL ~w~n", [Name]), bump(failed) ).
check_eq(Name, A, E) :- ( A == E -> bump(passed) ; format("FAIL ~w~n  got ~q  want ~q~n", [Name, A, E]), bump(failed) ).
report :-
    ( nb_current(passed, P) -> true ; P = 0 ), ( nb_current(failed, F) -> true ; F = 0 ),
    T is P + F, format("checks: ~d, passed: ~d, failed: ~d~n", [T, P, F]),
    ( F =:= 0 -> halt(0) ; halt(1) ).
out_text(T) :- ( nb_current(out, V) -> T = V ; T = "" ).
err_text(T) :- ( nb_current(err, V) -> T = V ; T = "" ).
write_out(T) :- out_text(P), string_concat(P, T, N), nb_setval(out, N).
write_err(T) :- err_text(P), string_concat(P, T, N), nb_setval(err, N).
read_fixture(_, "530070000\n600195000\n098000060\n800060003\n400803001\n700020006\n060000280\n000419005\n000080079\n").
capture(Args, Out, Err, Code) :-
    nb_setval(out, ""), nb_setval(err, ""),
    sudoku_runner:run(Args, harness:write_out, harness:write_err, harness:read_fixture, Code),
    out_text(Out), err_text(Err).
