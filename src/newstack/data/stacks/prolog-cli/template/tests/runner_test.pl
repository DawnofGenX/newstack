%% The output half: every row, every exit code, and the two writer closures.
:- module(runner_test, [run/0]).

:- use_module('../lib/runner.pl').
:- use_module('harness.pl').

run :-
    harness:run_cases(runner_test,
                      [usage_mentions_the_program,
                       single_file,
                       two_files_get_a_total,
                       columns_are_right_aligned,
                       figure_subset,
                       unreadable_file_still_reports,
                       every_operand_missing,
                       help_exits_zero,
                       version_exits_zero,
                       usage_error_exits_two]).

usage_mentions_the_program :-
    textstat_runner:program(Program),
    textstat_options:usage(Program, Usage),
    check('the usage text is named after the program',
          ( string_concat("Usage: ", Rest, Usage), string_concat(Program, _, Rest) )).

single_file :-
    tmp_file(plain, "alpha beta\ngamma delta\n", Path),
    capture([Path], Out, Err, Code),
    format(string(Expected), " 2  4 23 ~s\n", [Path]),
    check_eq('one file prints one row', Out, Expected),
    check_eq('one file says nothing on stderr', Err, ""),
    check_eq('one file exits zero', Code, 0).

two_files_get_a_total :-
    tmp_file(plain, "alpha beta\ngamma delta\n", First),
    tmp_file(tiny, "a\n", Second),
    capture([First, Second], Out, _, Code),
    format(string(Expected), " 2  4 23 ~s\n 1  1  2 ~s\n 3  5 25 total\n", [First, Second]),
    check_eq('two files get a total row', Out, Expected),
    check_eq('two readable files exit zero', Code, 0).

columns_are_right_aligned :-
    tmp_file(ten, "1\n2\n3\n4\n5\n6\n7\n8\n9\n10\n", Path),
    capture([Path], Out, _, _),
    format(string(Expected), "10 10 21 ~s\n", [Path]),
    check_eq('a two-digit figure widens every column', Out, Expected).

figure_subset :-
    tmp_file(plain, "alpha beta\ngamma delta\n", Path),
    capture(["-w", Path], Out, _, _),
    format(string(Expected), "4 ~s\n", [Path]),
    check_eq('-w prints one column', Out, Expected).

unreadable_file_still_reports :-
    tmp_file(plain, "alpha beta\ngamma delta\n", Path),
    tmp_path(missing, Missing),
    capture([Missing, Path], Out, Err, Code),
    format(string(Rows), " 2  4 23 ~s\n 2  4 23 total\n", [Path]),
    format(string(Complaint), "error: cannot open '~s'\n", [Missing]),
    check_eq('the readable row and its total still print', Out, Rows),
    check_eq('the unreadable file is named on stderr', Err, Complaint),
    check_eq('a partial failure exits one', Code, 1).

every_operand_missing :-
    tmp_path(missing, Missing),
    tmp_path(gone, Gone),
    capture([Missing, Gone], Out, Err, Code),
    check_eq('an all-missing run still totals to zero', Out, "0 0 0 total\n"),
    string_length(Err, ErrLength),
    check('both complaints reach stderr', ErrLength > 0),
    check_eq('an all-missing run exits one', Code, 1).

help_exits_zero :-
    capture(["--help"], Out, Err, Code),
    check('--help prints the usage', string_concat("Usage: ", _, Out)),
    check_eq('--help says nothing on stderr', Err, ""),
    check_eq('--help exits zero', Code, 0).

version_exits_zero :-
    capture(["--version"], Out, Err, Code),
    check_eq('--version prints the version', Out, "0.1.0\n"),
    check_eq('--version says nothing on stderr', Err, ""),
    check_eq('--version exits zero', Code, 0).

usage_error_exits_two :-
    capture(["--bogus"], Out, Err, Code),
    check_eq('a usage error prints no rows', Out, ""),
    check('the bad flag is named on stderr',
          sub_string(Err, _, _, _, "unknown option: --bogus")),
    check_eq('a usage error exits two', Code, 2).

tmp_path(Name, Path) :-
    getenv('NEWSTACK_TEST_TMP', Dir),
    atomic_list_concat([Dir, '/', Name, '.txt'], Path).

tmp_file(Name, Text, Path) :-
    tmp_path(Name, Path),
    setup_call_cleanup(open(Path, write, Stream, [encoding(utf8)]),
                       format(Stream, "~s", [Text]),
                       close(Stream)).
