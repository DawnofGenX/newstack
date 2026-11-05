%%% rebar3's escript entry point: the main module must be named after the
%%% application, so this module exists only to start it and park.
-module({{ package_name }}).
-export([main/1]).

main(_Args) ->
    {ok, _} = application:ensure_all_started({{ package_name }}),
    receive
        stop -> ok
    end.
