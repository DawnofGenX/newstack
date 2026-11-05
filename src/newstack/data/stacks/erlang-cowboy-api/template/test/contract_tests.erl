%%% Every status code the service can answer, pinned without a socket.
-module(contract_tests).
-include_lib("eunit/include/eunit.hrl").

health_test() ->
    ?assertEqual({200, #{<<"status">> => <<"ok">>}}, decode(contract:route(<<"GET">>, <<"/health">>, <<>>, <<>>))).

get_stats_test() ->
    ?assertEqual(
        {200, #{<<"text">> => <<"hello world\n">>, <<"lines">> => 1, <<"words">> => 2, <<"bytes">> => 12}},
        decode(contract:route(<<"GET">>, <<"/stats">>, <<"text=hello%20world%0A">>, <<>>))
    ).

get_stats_percent_decodes_the_whole_value_test() ->
    %% A raw "+" is a space in a query string, %09 is a tab, and %2B is a literal "+".
    ?assertEqual(
        {200, #{<<"text">> => <<"a b\tc">>, <<"lines">> => 0, <<"words">> => 3, <<"bytes">> => 5}},
        decode(contract:route(<<"GET">>, <<"/stats">>, <<"text=a+b%09c">>, <<>>))
    ),
    ?assertEqual(
        {200, #{<<"text">> => <<"a+b">>, <<"lines">> => 0, <<"words">> => 1, <<"bytes">> => 3}},
        decode(contract:route(<<"GET">>, <<"/stats">>, <<"text=a%2Bb">>, <<>>))
    ).

get_stats_without_text_test() ->
    ?assertEqual({422, #{<<"error">> => <<"missing_text">>}}, decode(contract:route(<<"GET">>, <<"/stats">>, <<>>, <<>>))).

get_stats_with_an_unrelated_parameter_test() ->
    ?assertEqual(
        {422, #{<<"error">> => <<"missing_text">>}},
        decode(contract:route(<<"GET">>, <<"/stats">>, <<"other=1">>, <<>>))
    ).

post_stats_test() ->
    ?assertEqual(
        {200, #{<<"text">> => <<"a b\nc\n">>, <<"lines">> => 2, <<"words">> => 3, <<"bytes">> => 6}},
        decode(contract:route(<<"POST">>, <<"/stats">>, <<>>, <<"{\"text\": \"a b\\nc\\n\"}">>))
    ).

post_stats_keeps_the_text_exactly_as_sent_test() ->
    ?assertEqual(
        {200, #{<<"text">> => <<"  padded  \n">>, <<"lines">> => 1, <<"words">> => 1, <<"bytes">> => 11}},
        decode(contract:route(<<"POST">>, <<"/stats">>, <<>>, <<"{\"text\": \"  padded  \\n\"}">>))
    ).

post_stats_with_a_non_string_text_test() ->
    ?assertEqual(
        {422, #{<<"error">> => <<"missing_text">>}},
        decode(contract:route(<<"POST">>, <<"/stats">>, <<>>, <<"{\"text\": 42}">>))
    ).

post_stats_without_text_test() ->
    ?assertEqual(
        {422, #{<<"error">> => <<"missing_text">>}},
        decode(contract:route(<<"POST">>, <<"/stats">>, <<>>, <<"{}">>))
    ).

post_stats_with_a_broken_body_test() ->
    ?assertEqual(
        {422, #{<<"error">> => <<"invalid_json">>}},
        decode(contract:route(<<"POST">>, <<"/stats">>, <<>>, <<"nope">>))
    ).

post_stats_with_a_json_array_body_test() ->
    ?assertEqual(
        {422, #{<<"error">> => <<"invalid_json">>}},
        decode(contract:route(<<"POST">>, <<"/stats">>, <<>>, <<"[1,2]">>))
    ).

wrong_method_on_a_known_path_test() ->
    ?assertEqual(
        {405, #{<<"error">> => <<"method_not_allowed">>}},
        decode(contract:route(<<"DELETE">>, <<"/health">>, <<>>, <<>>))
    ),
    ?assertEqual(
        {405, #{<<"error">> => <<"method_not_allowed">>}},
        decode(contract:route(<<"PUT">>, <<"/stats">>, <<>>, <<>>))
    ).

unknown_route_test() ->
    ?assertEqual(
        {404, #{<<"error">> => <<"not_found">>, <<"detail">> => <<"no route for GET /nope">>}},
        decode(contract:route(<<"GET">>, <<"/nope">>, <<>>, <<>>))
    ).

decode(#{status := Status, body := Body}) ->
    {Status, jsx:decode(Body, [return_maps])}.
