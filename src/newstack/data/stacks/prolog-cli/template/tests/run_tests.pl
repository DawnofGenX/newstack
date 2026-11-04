%% Entry point for `swipl -q -f tests/run_tests.pl`.
:- initialization(main, main).

:- use_module(library(filesex)).

:- prolog_load_context(directory, Here),
   forall(member(File, ['harness.pl', 'counts_test.pl', 'options_test.pl', 'runner_test.pl']),
          ( atomic_list_concat([Here, '/', File], Path),
            use_module(Path, []) )).

main :-
    tmp_dir(Dir),
    setenv('NEWSTACK_TEST_TMP', Dir),
    harness:reset,
    counts_test:run,
    options_test:run,
    runner_test:run,
    wipe(Dir),
    harness:report.

%% A scratch directory next to the tests, wiped before and after the run so a
%% stale fixture can never make a suite pass.
tmp_dir(Dir) :-
    working_directory(Cwd, Cwd),
    atomic_list_concat([Cwd, '/tests/.tmp'], Dir),
    wipe(Dir),
    make_directory_path(Dir).

wipe(Dir) :-
    (   exists_directory(Dir)
    ->  catch(delete_directory_and_contents(Dir), _, true)
    ;   true
    ).
