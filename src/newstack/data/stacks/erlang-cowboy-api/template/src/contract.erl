%%% The whole route table as a pure function: no sockets, no cowboy, so eunit
%%% can pin every status code and body.
-module(contract).
-export([route/4]).

-spec route(binary(), binary(), binary(), binary()) ->
          #{status := pos_integer(), body := binary()}.
route(<<"GET">>, <<"/health">>, _Query, _Body) ->
    reply(200, #{<<"status">> => <<"ok">>});
route(<<"GET">>, <<"/stats">>, Query, _Body) ->
    case query_param(Query, <<"text">>) of
        undefined -> error_reply(422, <<"missing_text">>, undefined);
        Text -> stats_reply(Text)
    end;
route(<<"POST">>, <<"/stats">>, _Query, Body) ->
    case decode_object(Body) of
        {ok, Object} ->
            case maps:get(<<"text">>, Object, undefined) of
                Text when is_binary(Text) -> stats_reply(Text);
                _ -> error_reply(422, <<"missing_text">>, undefined)
            end;
        error ->
            error_reply(422, <<"invalid_json">>, undefined)
    end;
route(_Method, Path, _Query, _Body) when Path =:= <<"/health">>; Path =:= <<"/stats">> ->
    error_reply(405, <<"method_not_allowed">>, undefined);
route(Method, Path, _Query, _Body) ->
    Detail = <<"no route for ", Method/binary, " ", Path/binary>>,
    error_reply(404, <<"not_found">>, Detail).

stats_reply(Text) ->
    Counts = counts:count(Text),
    reply(200, #{
        <<"text">> => Text,
        <<"lines">> => maps:get(lines, Counts),
        <<"words">> => maps:get(words, Counts),
        <<"bytes">> => maps:get(bytes, Counts)
    }).

reply(Status, Object) ->
    #{status => Status, body => jsx:encode(Object)}.

error_reply(Status, Code, undefined) ->
    reply(Status, #{<<"error">> => Code});
error_reply(Status, Code, Detail) ->
    reply(Status, #{<<"error">> => Code, <<"detail">> => Detail}).

decode_object(Body) ->
    try jsx:decode(Body, [return_maps]) of
        Object when is_map(Object) -> {ok, Object};
        _ -> error
    catch
        error:_ -> error
    end.

%% cowboy hands over the raw query string, so "text" arrives percent-encoded.
query_param(<<>>, _Name) ->
    undefined;
query_param(Query, Name) ->
    Pairs = binary:split(Query, <<"&">>, [global]),
    case [Value || Pair <- Pairs, Pair =/= <<>>, {Key, Value} <- [pair(Pair)], Key =:= Name] of
        [Value | _] -> unquote(Value);
        [] -> undefined
    end.

pair(Pair) ->
    case binary:split(Pair, <<"=">>) of
        [Key, Value] -> {Key, Value};
        [Key] -> {Key, <<>>}
    end.

unquote(Value) ->
    WithSpaces = for_each_plus(Value, <<>>),
    case unicode:characters_to_binary(uri_string:unquote(binary_to_list(WithSpaces))) of
        Decoded when is_binary(Decoded) -> Decoded
    end.

for_each_plus(<<>>, Acc) ->
    Acc;
for_each_plus(<<"+", Rest/binary>>, Acc) ->
    for_each_plus(Rest, <<Acc/binary, " ">>);
for_each_plus(<<Char, Rest/binary>>, Acc) ->
    for_each_plus(Rest, <<Acc/binary, Char>>).
