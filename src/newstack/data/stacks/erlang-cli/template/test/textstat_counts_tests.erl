-module(textstat_counts_tests).
-include_lib("eunit/include/eunit.hrl").

%% Two-byte letters: 14 bytes, 2 words, 1 line.
utf8_bytes() ->
    <<"h", 195, 169, "llo w", 195, 182, "rld\n">>.

empty_test() ->
    ?assertEqual({0, 0, 0}, textstat_counts:of_binary(<<"">>)).

one_line_test() ->
    ?assertEqual({2, 3, 17}, textstat_counts:of_binary(<<"alpha beta\ngamma\n">>)).

no_trailing_newline_test() ->
    ?assertEqual({0, 5, 29}, textstat_counts:of_binary(<<"one line, no trailing newline">>)).

utf8_is_counted_in_bytes_test() ->
    ?assertEqual({1, 2, 14}, textstat_counts:of_binary(utf8_bytes())).

all_whitespace_separates_words_test() ->
    ?assertEqual({1, 4, 8}, textstat_counts:of_binary(<<"a\tb", 11, "c", 12, "d\n">>)).

carriage_return_is_space_but_not_a_line_test() ->
    ?assertEqual({1, 2, 4}, textstat_counts:of_binary(<<"a\r\nb">>)).

add_test() ->
    ?assertEqual({5, 7, 9}, textstat_counts:add({1, 2, 3}, {4, 5, 6})).

columns_follow_the_asked_order_test() ->
    ?assertEqual([9, 7], textstat_counts:columns([c, l], {7, 8, 9})).

is_space_test() ->
    ?assert(lists:all(fun(B) -> textstat_counts:is_space(B) end, [32, 9, 10, 13, 11, 12])),
    ?assertNot(textstat_counts:is_space($a)),
    ?assertNot(textstat_counts:is_space(195)).
