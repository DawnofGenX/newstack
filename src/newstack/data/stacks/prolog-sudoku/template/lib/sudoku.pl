%% A constraint-free Sudoku solver: choose the most constrained empty cell,
%% try its legal candidates, and backtrack. Every rule is a plain predicate, so
%% the solver can be tested without any CLI or I/O machinery.
:- module(sudoku, [solve/2, parse_grid/2, format_grid/2, candidates/3, legal/3, parse_grid_lines/2]).

parse_grid_lines(Text, Lines) :-
    split_string(Text, "\n", "\r \t", All),
    exclude(==(""), All, Lines).

%% parse_grid(+Lines, -Grid): nine rows of nine digits ('.' for blank).
parse_grid(Lines, Grid) :-
    length(Lines, 9),
    maplist(parse_row, Lines, Grid),
    maplist(check_row_length, Grid).

parse_row(Line, Row) :-
    string_chars(Line, Chars),
    length(Chars, 9),
    maplist(parse_cell, Chars, Row).

parse_cell(., 0) :- !.
parse_cell(C, N) :- char_type(C, digit(N)), between(1, 9, N), !.

check_row_length(Row) :- length(Row, 9).

%% candidates(+Grid, +Index, -Values): legal digits at a zero cell.
candidates(Grid, I, Values) :-
    nth0(I, Grid, 0), !,
    I // 9 =:= Row, I mod 9 =:= Col,
    nth0(Row, Grid, ThisRow),
    findall(V, (between(1, 9, V), \+ member(V, ThisRow)), RowLeft),
    findall(V, (between(1, 9, R), R \= Row, nth0(R, Grid, Other), nth0(Col, Other, V), V > 0), ColUsed),
    BoxR is (Row // 3) * 3, BoxC is (Col // 3) * 3,
    findall(V, (between(0, 2, DR), between(0, 2, DC),
                BR is BoxR + DR, BC is BoxC + DC,
                nth0(BR, Grid, BoxRow), nth0(BC, BoxRow, V), V > 0), BoxUsed),
    append(ColUsed, BoxUsed, Used),
    exclude(=(0), RowLeft, A),
    exclude(in_list(Used), A, Values).

candidates(_, _, []).

in_list(List, X) :- memberchk(X, List).

%% legal(+Grid, -Complete, +I): internal recursive step.
legal(Grid, Complete, I) :-
    (   I >= 81 -> Complete = Grid
    ;   nth0(I, Grid, Cell),
        (   Cell > 0 -> Next is I + 1, legal(Grid, Complete, Next)
        ;   candidates(Grid, I, Values),
            member(V, Values),
            replace_at(Grid, I, V, Updated),
            Next is I + 1,
            legal(Updated, Complete, Next)
        )
    ).

replace_at(List, I, Value, Updated) :-
    nth0(I, List, _, Rest),
    nth0(I, Updated, Value, Rest).

solve(Grid, Solution) :- legal(Grid, Solution, 0).

format_grid(Grid, Lines) :-
    maplist(format_row, Grid, Lines).

format_row(Row, Line) :-
    maplist(cell_char, Row, Chars),
    string_chars(Line, Chars).

cell_char(0, '.') :- !.
cell_char(N, C) :- char_type(C, digit(N)).
