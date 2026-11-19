:- use_module('../tests/harness').
:- use_module('../lib/sudoku').
:- use_module('../lib/sudoku_runner').

:- initialization(main, main).

main(_) :-
    harness:reset,
    forall(member(Name, [grid_parse, candidates_count, solve_known, invalid_grid, format_roundtrip, cli_help, cli_usage, cli_solve]),
           ( catch(once(test(Name)), E, (print_message(error, E), fail)) -> true
           ; format("FAIL ~w~n", [Name]), harness:check(nop, true) )),
    harness:report.

grid_parse :-
    Lines = ["530070000","600195000","098000060","800060003","400803001","700020006","060000280","000419005","000080079"],
    sudoku:parse_grid(Lines, Grid),
    nth0(0, Grid, Row0),
    nth0(0, Row0, 5),
    nth0(1, Row0, 3),
    nth0(2, Row0, 0),
    harness:check('parse keeps digits and blanks', true).

candidates_count :-
    Lines = ["530070000","600195000","098000060","800060003","400803001","700020006","060000280","000419005","000080079"],
    sudoku:parse_grid(Lines, Grid),
    sudoku:candidates(Grid, 2, Values),
    Values == [1,2,4,7],
    harness:check('candidates respect row, column and box', true).

solve_known :-
    Lines = ["530070000","600195000","098000060","800060003","400803001","700020006","060000280","000419005","000080079"],
    sudoku:parse_grid(Lines, Grid),
    sudoku:solve(Grid, Solution),
    nth0(0, Solution, [5,3,4,6,7,8,9,1,2]),
    nth0(8, Solution, [4,8,7,1,9,6,3,5,2]),
    harness:check('known puzzle is solved', true).

invalid_grid :-
    \+ sudoku:parse_grid(["123"], _),
    harness:check('short grid is refused', true).

format_roundtrip :-
    sudoku:format_grid([[1,0,3,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0],
                        [0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0],
                        [0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0]], Lines),
    nth0(0, Lines, "1.3......"),
    harness:check('blanks render as dots', true).

cli_help :-
    harness:capture(['--help'], Out, _, Code),
    Code =:= 0,
    sub_string(Out, _, _, _, "Usage: {{ npm_name }}"),
    harness:check('help exits zero', true).

cli_usage :-
    harness:capture(['--bogus'], _, Err, Code),
    Code =:= 2,
    sub_string(Err, _, _, _, "unexpected argument"),
    harness:check('usage error exits two', true).

cli_solve :-
    harness:capture(['grid.txt'], Out, _, Code),
    Code =:= 0,
    sub_string(Out, _, _, _, "solutions: 1"),
    harness:check('fixture solves', true).
