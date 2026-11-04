%% The argv parser: every shape a user can type, including the ones that fail.
:- module(options_test, [run/0]).

:- use_module('../lib/options.pl').
:- use_module('harness.pl').

run :-
    harness:run_cases(options_test,
                      [defaults,
                       single_flags,
                       clustered_flags,
                       repeated_flags_are_ignored,
                       long_flags,
                       files_and_flags_mix,
                       dash_is_a_file,
                       terminator_makes_flags_into_files,
                       help_and_version_win,
                       unknown_long_flag,
                       unknown_short_flag,
                       version_string]).

defaults :-
    textstat_options:parse([], Parsed),
    check_eq('no flags means all three figures', Parsed, parsed(ok, [l, w, c], [], "")).

single_flags :-
    figure_of(["-l"], Lines),
    check_eq('-l asks for lines only', Lines, [l]),
    figure_of(["-w"], Words),
    check_eq('-w asks for words only', Words, [w]),
    figure_of(["-c"], Bytes),
    check_eq('-c asks for bytes only', Bytes, [c]).

clustered_flags :-
    figure_of(["-lw"], LinesWords),
    check_eq('a cluster asks for each of its letters', LinesWords, [l, w]),
    figure_of(["-lc"], LinesBytes),
    check_eq('a cluster keeps wc order, not the typed order', LinesBytes, [l, c]),
    figure_of(["-wlc"], All),
    check_eq('a full cluster is all three figures', All, [l, w, c]).

repeated_flags_are_ignored :-
    figure_of(["-l", "-l"], Once),
    check_eq('the same flag twice is still one column', Once, [l]).

long_flags :-
    figure_of(["--lines"], Lines),
    check_eq('--lines is a long -l', Lines, [l]),
    figure_of(["--bytes"], Bytes),
    check_eq('--bytes is a long -c', Bytes, [c]).

files_and_flags_mix :-
    textstat_options:parse(["a.txt", "-w", "b.txt"], Parsed),
    check_eq('flags may follow files', Parsed, parsed(ok, [w], ["a.txt", "b.txt"], "")).

dash_is_a_file :-
    textstat_options:parse(["-"], Parsed),
    check_eq('a lone dash is a file, not a flag', Parsed, parsed(ok, [l, w, c], ["-"], "")),
    textstat_options:parse(["-w", "-"], Width),
    check_eq('a dash after a flag is still an operand', Width, parsed(ok, [w], ["-"], "")).

terminator_makes_flags_into_files :-
    textstat_options:parse(["--", "-l"], Parsed),
    check_eq('after -- everything is a file', Parsed, parsed(ok, [l, w, c], ["-l"], "")),
    textstat_options:parse(["-w", "--", "--help"], Kept),
    check_eq('after -- the help text is a file name', Kept, parsed(ok, [w], ["--help"], "")).

help_and_version_win :-
    textstat_options:parse(["--help", "a.txt"], Help),
    check_eq('--help short-circuits the rest', Help, parsed(help, [], [], "")),
    textstat_options:parse(["-V"], Version),
    check_eq('-V reports the version', Version, parsed(version, [], [], "")).

unknown_long_flag :-
    textstat_options:parse(["--bogus"], Parsed),
    check_eq('an unknown long flag is a usage error', Parsed,
             parsed(usage_error, [], [], "unknown option: --bogus")).

unknown_short_flag :-
    textstat_options:parse(["-x"], Parsed),
    check_eq('an unknown short flag names itself', Parsed,
             parsed(usage_error, [], [], "unknown option: -x")),
    textstat_options:parse(["-lx"], Mixed),
    check_eq('a bad letter fails the whole cluster', Mixed,
             parsed(usage_error, [], [], "unknown option: -x")).

version_string :-
    textstat_options:tool_version(Version),
    check_eq('the tool version is a plain string', Version, "0.1.0").

figure_of(Args, Figures) :-
    textstat_options:parse(Args, Parsed),
    (   Parsed = parsed(ok, Figures0, _, _) -> Figures = Figures0 ; Figures = Parsed ).
