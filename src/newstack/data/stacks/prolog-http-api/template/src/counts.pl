:- module(counts, [count_text/2]).

%! count_text(+Text: string, -Counts: dict) is det.
%
%  wc rules: a line is a newline, a word is a maximal run of non-space
%  characters, and bytes are the UTF-8 bytes of the string.
count_text(Text, counts{lines: Lines, words: Words, bytes: Bytes}) :-
    string_codes(Text, Codes),
    count_lines(Codes, 0, Lines),
    count_words(Codes, false, 0, Words),
    count_bytes(Codes, 0, Bytes).

count_lines([], Acc, Acc).
count_lines([0'\n|Rest], Acc, Lines) :-
    Acc1 is Acc + 1,
    count_lines(Rest, Acc1, Lines).
count_lines([_|Rest], Acc, Lines) :-
    count_lines(Rest, Acc, Lines).

count_words([], _, Acc, Acc).
count_words([Code|Rest], InWord, Acc, Words) :-
    (   space_code(Code)
    ->  count_words(Rest, false, Acc, Words)
    ;   InWord == true
    ->  count_words(Rest, true, Acc, Words)
    ;   Acc1 is Acc + 1,
        count_words(Rest, true, Acc1, Words)
    ).

count_bytes([], Acc, Acc).
count_bytes([Code|Rest], Acc, Bytes) :-
    utf8_width(Code, Width),
    Acc1 is Acc + Width,
    count_bytes(Rest, Acc1, Bytes).

utf8_width(Code, 1) :- Code < 0x80, !.
utf8_width(Code, 2) :- Code < 0x800, !.
utf8_width(Code, 3) :- Code < 0x10000, !.
utf8_width(_, 4).

space_code(0' ). space_code(0'\t). space_code(0'\n). space_code(0'\r).
space_code(0'\v). space_code(0'\f).
