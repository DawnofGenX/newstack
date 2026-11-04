%% Hand-rolled argv parser: no library dependency, no exceptions for bad input.
:- module(textstat_options, [parse/2, usage/2, tool_version/1]).

tool_version("0.1.0").

parse(Args, Parsed) :-
    walk(Args, flags, state(ok, no, no, no, [], ""), End),
    End = state(Status, L, W, C, FilesRev, Message),
    reverse(FilesRev, Files),
    (   Status == ok
    ->  figures_in_order(L, W, C, Figures),
        Parsed = parsed(ok, Figures, Files, "")
    ;   Parsed = parsed(Status, [], [], Message)
    ).

figures_in_order(no, no, no, [l, w, c]) :- !.
figures_in_order(L, W, C, Figures) :-
    findall(Figure, (member(Figure-Flag, [l-L, w-W, c-C]), Flag == yes), Figures).

walk([], _, State, State).
walk(_, _, State, State) :- State = state(Status, _, _, _, _, _), Status \== ok, !.
walk(["--" | Rest], flags, State0, State) :- !, walk(Rest, literal, State0, State).
walk([Arg | Rest], Mode, State0, State) :-
    (   Mode == literal
    ->  add_file(Arg, Rest, State0, State)
    ;   Arg == "-"
    ->  add_file("-", Rest, State0, State)
    ;   string_concat("--", Name, Arg)
    ->  long_flag(Name, Rest, State0, State)
    ;   string_concat("-", Letters, Arg)
    ->  string_chars(Letters, Chars),
        flag_chars(Chars, Rest, State0, State)
    ;   add_file(Arg, Rest, State0, State)
    ).

add_file(File, Rest, state(S, L, W, C, Files, M), State) :-
    walk(Rest, flags, state(S, L, W, C, [File | Files], M), State).

long_flag(Name, Rest, State0, State) :-
    State0 = state(S, L, W, C, Files, M),
    (   long_figure(Name, Figure)
    ->  set_figure(Figure, state(S, L, W, C, Files, M), State1),
        walk(Rest, flags, State1, State)
    ;   Name == "help"
    ->  walk(Rest, flags, state(help, L, W, C, Files, M), State)
    ;   Name == "version"
    ->  walk(Rest, flags, state(version, L, W, C, Files, M), State)
    ;   string_concat("unknown option: --", Name, Message),
        walk(Rest, flags, state(usage_error, L, W, C, Files, Message), State)
    ).

long_figure("lines", l).
long_figure("words", w).
long_figure("bytes", c).

flag_chars([], Rest, State0, State) :- walk(Rest, flags, State0, State).
flag_chars([_|_], _, State, State) :- State = state(Status, _, _, _, _, _), Status \== ok, !.
flag_chars([Char | More], Rest, State0, State) :-
    State0 = state(S, L, W, C, Files, M),
    (   short_figure(Char, Figure)
    ->  set_figure(Figure, state(S, L, W, C, Files, M), State1),
        flag_chars(More, Rest, State1, State)
    ;   Char == 'h'
    ->  flag_chars(More, Rest, state(help, L, W, C, Files, M), State)
    ;   Char == 'V'
    ->  flag_chars(More, Rest, state(version, L, W, C, Files, M), State)
    ;   string_concat("unknown option: -", Char, Message),
        flag_chars(More, Rest, state(usage_error, L, W, C, Files, Message), State)
    ).

short_figure('l', l).
short_figure('w', w).
short_figure('c', c).

set_figure(l, state(S, _, W, C, Files, M), state(S, yes, W, C, Files, M)).
set_figure(w, state(S, L, _, C, Files, M), state(S, L, yes, C, Files, M)).
set_figure(c, state(S, L, W, _, Files, M), state(S, L, W, yes, Files, M)).

usage(Program, Text) :-
    format(string(Text),
           "Usage: ~w [OPTION]... [FILE]...\nCount lines, words and bytes.\n\n  -l, --lines    print the line count\n  -w, --words    print the word count\n  -c, --bytes    print the byte count\n  -h, --help     show this help and exit\n  -V, --version  show the version and exit\n\nWith no FILE, or when FILE is -, read standard input.\n",
           [Program]).
