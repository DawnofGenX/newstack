%% Entry point: the only file touching real streams and exit status.
:- prolog_load_context(directory, Here),
   atomic_list_concat([Here, '/lib/runner.pl'], Runner),
   use_module(Runner).

:- initialization(main, main).

main :-
    current_prolog_flag(argv, Argv),
    maplist(as_string, Argv, Args),
    sudoku_runner:run(Args, stdout_msg, stderr_msg, read_grid_file, Code),
    halt(Code).

as_string(Value, Text) :- ( string(Value) -> Text = Value ; atom_string(Value, Text) ).
stdout_msg(Text) :- format(current_output, "~w", [Text]).
stderr_msg(Text) :- format(user_error, "~w", [Text]).
read_grid_file(Path, Text) :- read_file_to_string(Path, Text, []).
