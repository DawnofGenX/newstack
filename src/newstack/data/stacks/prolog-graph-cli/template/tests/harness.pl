%% Harness copied style.
:- module(harness, [reset/0, check/2, check_eq/3, report/0, run_cases/2]).
reset :- nb_setval(passed,0), nb_setval(failed,0).
bump(K) :- (nb_current(K,V)->N is V+1;N=1), nb_setval(K,N).
check(Name, Goal) :- (catch(call(Goal),_,fail) -> bump(passed); format("FAIL ~w~n",[Name]), bump(failed)).
check_eq(Name, A, E) :- (A == E -> bump(passed); format("FAIL ~w~n  got ~q expected ~q~n",[Name,A,E]), bump(failed)).
run_cases(Module, Cases) :-
    forall(member(Name, Cases),
           (   catch(once(call(Module:Name)), Error, (print_message(error, Error), fail))
           ->  true
           ;   format("FAIL ~w~n", [Name]), bump(failed)
           )).
report :- (nb_current(passed,P)->true;P=0), (nb_current(failed,F)->true;F=0), T is P+F, format("checks: ~d, passed: ~d, failed: ~d~n",[T,P,F]), (F=:=0 -> halt(0); halt(1)).
