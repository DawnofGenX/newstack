%% Entry point.
:- initialization(main, main).

:- prolog_load_context(directory, Here),
   atomic_list_concat([Here, '/lib/graph.pl'], GraphPath),
   use_module(GraphPath).

main :-
    current_prolog_flag(argv, Argv),
    maplist(as_string, Argv, Args),
    graph_cli:run(Args, write_stdout, write_stderr, Code),
    halt(Code).

as_string(Value, Text) :-
    (   string(Value) -> Text = Value ; atom_string(Value, Text) ).

write_stdout(Text) :- format(current_output, "~s", [Text]).
write_stderr(Text) :- format(user_error, "~s", [Text]).
