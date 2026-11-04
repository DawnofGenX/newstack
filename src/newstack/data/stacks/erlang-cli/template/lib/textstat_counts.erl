%% Counting that matches `wc -l -w -c`, byte for byte.
%%
%% Everything works on binaries, because a "character" is a locale question and
%% `wc` answers it in bytes.
-module(textstat_counts).
-export([of_binary/1, add/2, columns/2, is_space/1]).
-export_type([counts/0]).

-type counts() :: {non_neg_integer(), non_neg_integer(), non_neg_integer()}.

-spec is_space(byte()) -> boolean().
is_space($\s) -> true;
is_space($\t) -> true;
is_space($\n) -> true;
is_space($\r) -> true;
is_space(11) -> true;  % vertical tab
is_space(12) -> true;  % form feed
is_space(_) -> false.

-spec of_binary(binary()) -> counts().
of_binary(Data) ->
    {Lines, Words, _Bytes, _InWord} =
        lists:foldl(fun step/2, {0, 0, byte_size(Data), false}, binary_to_list(Data)),
    {Lines, Words, byte_size(Data)}.

step(Byte, {Lines, Words, Bytes, InWord}) ->
    Lines1 = case Byte of
                 $\n -> Lines + 1;
                 _ -> Lines
             end,
    case {is_space(Byte), InWord} of
        {true, _} -> {Lines1, Words, Bytes, false};
        {false, true} -> {Lines1, Words, Bytes, true};
        {false, false} -> {Lines1, Words + 1, Bytes, true}
    end.

-spec add(counts(), counts()) -> counts().
add({L1, W1, B1}, {L2, W2, B2}) -> {L1 + L2, W1 + W2, B1 + B2}.

%% @doc The figures the caller asked for, in the order they were asked for.
-spec columns([l | w | c], counts()) -> [non_neg_integer()].
columns(Figures, {Lines, Words, Bytes}) ->
    [column(Figure, Lines, Words, Bytes) || Figure <- Figures].

column(l, Lines, _Words, _Bytes) -> Lines;
column(w, _Lines, Words, _Bytes) -> Words;
column(c, _Lines, _Words, Bytes) -> Bytes.
