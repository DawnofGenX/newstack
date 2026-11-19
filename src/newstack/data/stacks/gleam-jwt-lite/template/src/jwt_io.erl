%% OTP bridge: argv, exit status, base64url and HMAC-SHA256.
%% Calling Erlang modules through @external keeps the Gleam side dependency
%% free -- crypto and base64 ship with OTP, no hex packages are fetched.
-module(jwt_io).
-export([args/0, halt/1, b64url_encode/1, b64url_decode/1, hmac_sha256/2]).

args() ->
    [unicode:characters_to_binary(A) || A <- init:get_plain_arguments()].

halt(Code) when is_integer(Code) -> erlang:halt(Code).

%% RFC 4648 base64url without padding.
b64url_encode(Data) when is_binary(Data) ->
    Enc = base64:encode(Data, #{urlsafe => true}),
    binary:replace(Enc, <<"=">>, <<>>, [global]).

b64url_decode(Text) when is_binary(Text) ->
    Missing = (4 - (byte_size(Text) rem 4)) rem 4,
    Padding = binary:copy(<<"=">>, Missing),
    base64:decode(<<Text/binary, Padding/binary>>, #{urlsafe => true}).

hmac_sha256(Key, Data) when is_binary(Key), is_binary(Data) ->
    _ = application:ensure_all_started(crypto),
    crypto:mac(hmac, sha256, Key, Data).
