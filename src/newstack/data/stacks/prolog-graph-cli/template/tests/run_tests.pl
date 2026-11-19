%% Entry point.
:- initialization(main, main).

:- prolog_load_context(directory, Here),
   forall(member(File, ['harness.pl', 'graph_test.pl']),
          ( atomic_list_concat([Here, '/', File], Path),
            use_module(Path, []) )).

main :-
    harness:reset,
    graph_test:run,
    harness:report.
