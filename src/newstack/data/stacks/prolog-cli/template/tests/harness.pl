%% A four-predicate harness: no framework, no dependencies, one honest tally.
:- module(harness, [reset/0, check/2, check_eq/3, report/0, capture/4, run_cases/2, out_text/1, err_text/1]).

reset :-
    nb_setval(passed, 0),
    nb_setval(failed, 0),
    nb_setval(out, ""),
    nb_setval(err, "").

bump(Key) :-
    (   nb_current(Key, Value) -> Next is Value + 1 ; Next = 1 ),
    nb_setval(Key, Next).

check(Name, Goal) :-
    (   catch(call(Goal), Error, ( print_message(error, Error), fail ))
    ->  bump(passed)
    ;   format("FAIL ~w~n", [Name]),
        bump(failed)
    ).

check_eq(Name, Actual, Expected) :-
    (   Actual == Expected
    ->  bump(passed)
    ;   format("FAIL ~w~n  got      ~q~n  expected ~q~n", [Name, Actual, Expected]),
        bump(failed)
    ).

report :-
    ( nb_current(passed, Passed) -> true ; Passed = 0 ),
    ( nb_current(failed, Failed) -> true ; Failed = 0 ),
    Total is Passed + Failed,
    format("checks: ~d, passed: ~d, failed: ~d~n", [Total, Passed, Failed]),
    (   Failed =:= 0 -> halt(0) ; halt(1) ).

%% Run a suite's cases one by one: a case that throws or fails is reported once
%% and the run continues, so one broken case cannot replay the whole suite.
run_cases(Module, Cases) :-
    forall(member(Name, Cases),
           (   catch(once(call(Module:Name)), Error, (print_message(error, Error), fail))
           ->  true
           ;   format("FAIL ~w~n", [Name]),
               bump(failed)
           )).

out_text(Text) :- ( nb_current(out, Value) -> Text = Value ; Text = "" ).
err_text(Text) :- ( nb_current(err, Value) -> Text = Value ; Text = "" ).

write_out(Text) :-
    out_text(Previous),
    string_concat(Previous, Text, Next),
    nb_setval(out, Next).

write_err(Text) :-
    err_text(Previous),
    string_concat(Previous, Text, Next),
    nb_setval(err, Next).

%% Run the CLI against a fake pair of writers, so the whole output contract is
%% checked without touching stdout.
capture(Args, Out, Err, Code) :-
    nb_setval(out, ""),
    nb_setval(err, ""),
    textstat_runner:run(Args, harness:write_out, harness:write_err, Code),
    out_text(Out),
    err_text(Err).
