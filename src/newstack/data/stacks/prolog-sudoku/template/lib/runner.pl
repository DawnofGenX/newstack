%% CLI core with injected output and file reader, so it is unit-testable.
:- module(sudoku_runner, [run/5, program_name/1]).
:- use_module(options).
:- use_module(sudoku).

program_name('{{ npm_name }}').

run(Args, Out, Err, ReadFile, Code) :-
    options:parse_options(Args, Opts),
    Status = Opts.status,
    (   Status =:= 1
    ->  call(Out, "Solve a Sudoku puzzle from a nine-line grid.\n"),
        format(atom(Atom), "Usage: ~w [--limit N] FILE~n", ['{{ npm_name }}']),
        call(Out, Atom),
        Code = 0
    ;   Status =:= 2
    ->  format(atom(M1), "~w: ~w~n", ['{{ npm_name }}', Opts.message]),
        call(Err, M1),
        format(atom(M2), "Try '~w --help' for more information.~n", ['{{ npm_name }}']),
        call(Err, M2),
        Code = 2
    ;   catch(call(ReadFile, Opts.path, Text), Error,
              ( format(atom(E), "error: ~w~n", [Error]), call(Err, E), fail ))
    ->  sudoku:parse_grid_lines(Text, Lines),
        (   sudoku:parse_grid(Lines, Grid)
        ->  findall(S, (sudoku:solve(Grid, S), limit(Opts.limit, S == S)), Solutions),
            length(Solutions, Count),
            format(atom(Head), "solutions: ~d~n", [Count]),
            call(Out, Head),
            forall(nth0(I, Solutions, Sol),
                   ( format(atom(Title), "solution ~d~n", [I]), call(Out, Title),
                     sudoku:format_grid(Sol, Rows),
                     forall(member(Row, Rows), (format(atom(L), "~w~n", [Row]), call(Out, L))) )),
            Code = 0
        ;   call(Err, "error: expected nine rows of nine cells\n"),
            Code = 1
        )
    ;   Code = 1
    ).
