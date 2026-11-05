%%% One cowboy handler for every route: contract:route/4 owns the table.
-module(stat_handler).
-export([init/2]).

init(Req0, State) ->
    Method = cowboy_req:method(Req0),
    {Body, Req1} = read_body(Req0),
    Reply = contract:route(Method, cowboy_req:path(Req1), cowboy_req:qs(Req1), Body),
    Req2 = cowboy_req:reply(
        maps:get(status, Reply),
        #{<<"content-type">> => <<"application/json">>},
        maps:get(body, Reply),
        Req1
    ),
    {ok, Req2, State}.

read_body(Req0) ->
    case cowboy_req:read_body(Req0, #{length => 65536, period => 5000}) of
        {ok, Body, Req1} -> {Body, Req1};
        {more, _Partial, Req1} -> {<<>>, Req1}
    end.
