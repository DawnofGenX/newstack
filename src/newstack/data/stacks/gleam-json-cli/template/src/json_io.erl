-module(json_io).
-export([args/0, read_stdin/0]).

args() ->
    [unicode:characters_to_binary(A) || A <- init:get_plain_arguments()].

read_stdin() ->
    io:setopts(standard_io, [binary, {encoding, utf8}]),
    iolist_to_binary(read_acc([])).

read_acc(Acc) ->
    case io:get_line("") of
        eof -> lists:reverse(Acc);
        {error, _} -> lists:reverse(Acc);
        {ok, Line} -> read_acc([Line | Acc]);
        Line when is_binary(Line) -> read_acc([Line | Acc])
    end.