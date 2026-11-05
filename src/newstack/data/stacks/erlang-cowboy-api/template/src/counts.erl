%%% wc-style counting: line = a "\n" byte, word = maximal run of non-space,
%%% bytes = the UTF-8 length. `of` is reserved in Erlang (bit syntax), so the
%%% entry point is `count/1`.
-module(counts).
-export([count/1]).

-type counts() :: #{lines := non_neg_integer(), words := non_neg_integer(),
                    bytes := non_neg_integer()}.
-export_type([counts/0]).

-spec count(binary()) -> counts().
count(Text) when is_binary(Text) ->
    {Lines, Words, _InWord} = lists:foldl(fun step/2, {0, 0, false}, binary_to_list(Text)),
    #{lines => Lines, words => Words, bytes => byte_size(Text)}.

step($\n, {Lines, Words, _InWord}) ->
    {Lines + 1, Words, false};
step(Char, {Lines, Words, InWord}) ->
    case is_space(Char) of
        true ->
            {Lines, Words, false};
        false when InWord ->
            {Lines, Words, true};
        false ->
            {Lines, Words + 1, true}
    end.

is_space(32) -> true;   % space
is_space(9) -> true;    % tab
is_space(13) -> true;   % carriage return
is_space(11) -> true;   % vertical tab
is_space(12) -> true;   % form feed
is_space(_) -> false.
