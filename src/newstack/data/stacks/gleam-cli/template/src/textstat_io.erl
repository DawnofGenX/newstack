-module(textstat_io).
-export([args/0, read_stdin/0]).

%% Command-line arguments (the words after `gleam run --`) as a list of UTF-8
%% binaries. init:get_plain_arguments/0 returns charlists of codepoints, so
%% each is converted to a UTF-8 binary to preserve byte-accurate paths.
args() ->
    [unicode:characters_to_binary(A) || A <- init:get_plain_arguments()].

%% All of stdin as a single binary. The @@main runner sets standard_io to
%% binary/utf8, but that option is set in the main process; the program runs
%% in a spawned process with its own io server, so set it here before reading.
%% io:get_line/1 returns binaries; read until eof.
read_stdin() ->
    io:setopts(standard_io, [binary, {encoding, utf8}]),
    iolist_to_binary(read_acc([])).

%% In binary mode io:get_line/1 hands back the line itself as a binary; some
%% OTP releases wrap it in {ok, Line}, so accept both shapes.
read_acc(Acc) ->
    case io:get_line("") of
        eof -> lists:reverse(Acc);
        {error, _} -> lists:reverse(Acc);
        {ok, Line} -> read_acc([Line | Acc]);
        Line when is_binary(Line) -> read_acc([Line | Acc])
    end.
