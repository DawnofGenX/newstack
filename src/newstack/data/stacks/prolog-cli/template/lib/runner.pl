%% All process I/O lives behind the two writer closures passed to run/4, so the
%% whole output contract can be exercised without touching a file descriptor.
:- module(textstat_runner, [run/4, program/1, version/1]).

:- prolog_load_context(directory, Here),
   atomic_list_concat([Here, '/counts.pl'], CountsPath),
   atomic_list_concat([Here, '/options.pl'], OptionsPath),
   use_module(CountsPath),
   use_module(OptionsPath).

program("{{ npm_name }}").

version(Version) :- textstat_options:tool_version(Version).

run(Args, Out, Err, Code) :-
    textstat_options:parse(Args, Parsed),
    Parsed = parsed(Status, Figures, Files, Message),
    run_status(Status, Figures, Files, Message, Out, Err, Code).

run_status(help, _, _, _, Out, _, Code) :-
    program(Program),
    textstat_options:usage(Program, Text),
    call(Out, Text),
    Code = 0.
run_status(version, _, _, _, Out, _, Code) :-
    version(Version),
    format(string(Text), "~s\n", [Version]),
    call(Out, Text),
    Code = 0.
run_status(usage_error, _, _, Message, _, Err, Code) :-
    program(Program),
    format(string(Text), "~w: ~s\n", [Program, Message]),
    format(string(Hint), "Try '~w --help' for more information.\n", [Program]),
    call(Err, Text),
    call(Err, Hint),
    Code = 2.
run_status(ok, Figures, Files, _, Out, Err, Code) :-
    operands(Files, Operands),
    read_operands(Operands, Figures, Err, Rows, Failed),
    (   Failed =:= 0 -> Code = 0 ; Code = 1 ),
    length(Operands, OperandCount),
    total_counts(Rows, Total),
    (   OperandCount > 1 -> append(Rows, [total(Total)], AllRows) ; AllRows = Rows ),
    width_of(AllRows, Figures, Width),
    print_rows(AllRows, Figures, Width, Out).

operands([], ["-"]).
operands(Files, Files).

read_operands(Operands, Figures, Err, Rows, Failed) :-
    foldl(read_operand(Figures, Err), Operands, rows([], 0), rows(RowsRev, Failed)),
    reverse(RowsRev, Rows).

read_operand(Figures, Err, Label, rows(Rows0, Failed0), rows(Rows, Failed)) :-
    read_counts(Label, Result),
    (   Result = ok(Counts)
    ->  textstat_counts:columns(Figures, Counts, Values),
        Rows = [row(Label, Values, Counts) | Rows0],
        Failed = Failed0
    ;   format(string(Text), "error: cannot open '~s'\n", [Label]),
        call(Err, Text),
        Rows = Rows0,
        Failed is Failed0 + 1
    ).

read_counts("-", Result) :- !,
    (   catch(textstat_counts:of_stdin(Counts), _, fail)
    ->  Result = ok(Counts)
    ;   Result = error(no_input)
    ).
read_counts(Path, Result) :-
    textstat_counts:of_file(Path, Result).

total_counts([], counts(0, 0, 0)).
total_counts(Rows, Total) :-
    foldl(sum_row, Rows, counts(0, 0, 0), Total).

sum_row(row(_, _, Counts), Acc, Next) :-
    textstat_counts:add(Acc, Counts, Next).

%% wc right-aligns every printed row to the same width, the total row included.
width_of(AllRows, Figures, Width) :-
    findall(Digits,
            ( member(Row, AllRows),
              row_values(Row, Figures, Values),
              member(Value, Values),
              digit_count(Value, Digits) ),
            All),
    (   All == [] -> Width = 1 ; max_list(All, Width) ).

row_values(row(_, Values, _), _, Values).
row_values(total(Counts), Figures, Values) :-
    textstat_counts:columns(Figures, Counts, Values).

print_rows(Rows, Figures, Width, Out) :-
    forall(member(Row, Rows), print_row(Row, Figures, Width, Out)).

print_row(Row, Figures, Width, Out) :-
    row_values(Row, Figures, Values),
    row_label(Row, Label),
    findall(Padded, (member(Value, Values), pad(Value, Width, Padded)), Cells),
    atomic_list_concat(Cells, " ", Body),
    format(string(Text), "~s ~s\n", [Body, Label]),
    call(Out, Text).

row_label(row(Label, _, _), Label).
row_label(total(_), "total").

digit_count(Value, Digits) :-
    format(string(Text), "~d", [Value]),
    string_length(Text, Digits).

pad(Value, Width, Padded) :-
    digit_count(Value, Digits),
    Gap is Width - Digits,
    (   Gap =< 0
    ->  format(string(Padded), "~d", [Value])
    ;   length(Blanks, Gap),
        maplist(=(0' ), Blanks),
        string_chars(Padding, Blanks),
        format(string(Padded), "~s~d", [Padding, Value])
    ).
