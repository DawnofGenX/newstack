%%% The counting rules, pinned: line = "\n", word = maximal run of non-space,
%%% bytes = UTF-8 length ("héllo" is 5 characters but 6 bytes).
-module(counts_tests).
-include_lib("eunit/include/eunit.hrl").

counts_test_() ->
    [
        ?_assertEqual(#{lines => 1, words => 2, bytes => 12}, counts:count(<<"hello world\n">>)),
        ?_assertEqual(#{lines => 0, words => 0, bytes => 0}, counts:count(<<>>)),
        ?_assertEqual(#{lines => 3, words => 1, bytes => 4}, counts:count(<<"\n\nx\n">>)),
        ?_assertEqual(#{lines => 0, words => 0, bytes => 4}, counts:count(<<"  \t ">>)),
        ?_assertEqual(#{lines => 0, words => 1, bytes => 3}, counts:count(<<"abc">>)),
        ?_assertEqual(#{lines => 1, words => 2, bytes => 14}, counts:count(<<"héllo wörld\n"/utf8>>)),
        ?_assertEqual(#{lines => 1, words => 1, bytes => 5}, counts:count(<<"🙂\n"/utf8>>))
    ].

count_rejects_a_non_binary_test() ->
    ?assertError(function_clause, counts:count("hello")).
