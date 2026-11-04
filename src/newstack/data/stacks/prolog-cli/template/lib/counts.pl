%% Byte-exact counting core: no I/O policy, just a stream in and a tally out.
:- module(textstat_counts, [empty/1, add/3, columns/3, is_space/1, of_stream/2, of_file/2, of_stdin/1]).

empty(counts(0, 0, 0)).

add(counts(L1, W1, B1), counts(L2, W2, B2), counts(L, W, B)) :-
    L is L1 + L2,
    W is W1 + W2,
    B is B1 + B2.

%% Whitespace as wc defines it for the C locale.
is_space(32).  % space
is_space(9).   % tab
is_space(10).  % newline
is_space(13).  % carriage return
is_space(11).  % vertical tab
is_space(12).  % form feed

columns(Figures, counts(L, W, B), Values) :-
    findall(V, (member(F, Figures), figure_value(F, L, W, B, V)), Values).

figure_value(l, L, _, _, L).
figure_value(w, _, W, _, W).
figure_value(c, _, _, B, B).

of_stream(Stream, Counts) :-
    count_loop(Stream, 0, 0, 0, 0, Counts).

count_loop(Stream, Lines0, Words0, Bytes0, InWord0, Counts) :-
    get_byte(Stream, Byte),
    (   Byte =:= -1
    ->  Counts = counts(Lines0, Words0, Bytes0)
    ;   (   Byte =:= 10 -> Lines is Lines0 + 1 ; Lines = Lines0 ),
        count_word(Byte, InWord0, Words0, Words, InWord),
        Bytes is Bytes0 + 1,
        count_loop(Stream, Lines, Words, Bytes, InWord, Counts)
    ).

%% A word starts when a non-space byte follows a space byte; a trailing run is
%% therefore already counted by the time the stream ends.
count_word(Byte, InWord0, Words0, Words, InWord) :-
    (   is_space(Byte)
    ->  Words = Words0, InWord = 0
    ;   InWord = 1,
        (   InWord0 =:= 0 -> Words is Words0 + 1 ; Words = Words0 )
    ).

of_file(Path, Result) :-
    catch(( setup_call_cleanup(open(Path, read, Stream, [type(binary)]),
                               of_stream(Stream, Counts),
                               close(Stream)),
            Result = ok(Counts) ),
          Error,
          Result = error(Error)).

of_stdin(Counts) :-
    open('/dev/stdin', read, Stream, [type(binary)]),
    setup_call_cleanup(true, of_stream(Stream, Counts), close(Stream)).
