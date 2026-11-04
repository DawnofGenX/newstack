%% The counting core: every rule wc applies, checked against a scratch file so
%% the bytes go through a real stream.
:- module(counts_test, [run/0]).

:- use_module('../lib/counts.pl').
:- use_module('harness.pl').

run :-
    harness:run_cases(counts_test,
                      [empty_tally,
                       whitespace_set,
                       plain_text,
                       missing_final_newline,
                       control_bytes_are_separators,
                       multibyte_bytes,
                       carriage_return_is_not_a_line_break,
                       tally_addition,
                       column_selection,
                       unreadable_file_is_an_error]).

empty_tally :-
    textstat_counts:empty(Counts),
    check_eq('an empty tally is all zeroes', Counts, counts(0, 0, 0)).

whitespace_set :-
    findall(Byte, textstat_counts:is_space(Byte), Bytes),
    check_eq('the whitespace set is wc\'s six bytes', Bytes, [32, 9, 10, 13, 11, 12]),
    check('a letter is not whitespace', \+ textstat_counts:is_space(65)),
    check('a nul byte is not whitespace', \+ textstat_counts:is_space(0)).

plain_text :-
    count_of("alpha beta\ngamma delta\n", Counts),
    check_eq('two lines, four words, twenty-three bytes', Counts, counts(2, 4, 23)).

missing_final_newline :-
    count_of("alpha beta\ngamma delta", Counts),
    check_eq('a missing final newline costs a line, not a word', Counts, counts(1, 4, 22)).

control_bytes_are_separators :-
    count_of("a\tb\vc\fd\n", Counts),
    check_eq('tab, vertical tab and form feed all separate words', Counts, counts(1, 4, 8)).

multibyte_bytes :-
    count_of("héllo wörld\n", Counts),
    check_eq('bytes are counted, not characters', Counts, counts(1, 2, 14)).

carriage_return_is_not_a_line_break :-
    count_of("a\rb\n", Counts),
    check_eq('a bare carriage return separates words but starts no line', Counts, counts(1, 2, 4)).

tally_addition :-
    textstat_counts:empty(Zero),
    textstat_counts:add(Zero, counts(2, 4, 23), Doubled),
    textstat_counts:add(Doubled, counts(2, 4, 23), Counts),
    check_eq('tallies add element-wise', Counts, counts(4, 8, 46)).

column_selection :-
    textstat_counts:columns([l, w, c], counts(2, 4, 23), All),
    check_eq('all three columns in wc order', All, [2, 4, 23]),
    textstat_counts:columns([c, l], counts(2, 4, 23), Reordered),
    check_eq('a subset keeps the order it was asked for', Reordered, [23, 2]),
    textstat_counts:columns([], counts(2, 4, 23), None),
    check_eq('no figures means no columns', None, []).

unreadable_file_is_an_error :-
    textstat_counts:of_file("definitely-not-here.txt", Result),
    check('a missing file is reported, not thrown', Result = error(_)).

%% Write Text to a scratch file under tests/.tmp and count it back.
count_of(Text, Counts) :-
    tmp_path("counts", Path),
    write_bytes(Path, Text),
    textstat_counts:of_file(Path, Result),
    (   Result = ok(Found) -> Counts = Found ; Counts = unexpected(Result) ).

write_bytes(Path, Text) :-
    setup_call_cleanup(open(Path, write, Stream, [encoding(utf8)]),
                       format(Stream, "~s", [Text]),
                       close(Stream)).

tmp_path(Name, Path) :-
    getenv('NEWSTACK_TEST_TMP', Dir),
    atomic_list_concat([Dir, '/', Name, '.txt'], Path).
