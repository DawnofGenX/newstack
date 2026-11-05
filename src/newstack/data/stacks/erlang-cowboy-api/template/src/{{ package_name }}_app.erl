-module({{ package_name }}_app).
-behaviour(application).
-export([start/2, stop/1]).

start(_Type, _Args) ->
    Dispatch = cowboy_router:compile([{'_', [{"/[...]", stat_handler, []}]}]),
    {ok, _} = cowboy:start_clear(listener, [{port, port()}], #{env => #{dispatch => Dispatch}}),
    {{ package_name }}_sup:start_link().

stop(_State) ->
    ok.

port() ->
    case os:getenv("PORT") of
        false -> 8080;
        Value -> list_to_integer(Value)
    end.
