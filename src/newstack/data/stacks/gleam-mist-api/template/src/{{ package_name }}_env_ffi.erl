%% Reads an environment variable. Gleam's stdlib has no `os:getenv` binding, so
%% the port lookup goes through this three-line module.
-module({{ package_name }}_env_ffi).

-export([get_env/1]).

-spec get_env(binary()) -> {ok, binary()} | {error, nil}.
get_env(Name) ->
    case os:getenv(binary_to_list(Name)) of
        false -> {error, nil};
        Value -> {ok, list_to_binary(Value)}
    end.
