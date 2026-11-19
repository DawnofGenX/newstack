%% The only module that touches the real process: files, stdin, stdout, exit.
-module(textstat_main).
-export([run/0]).

-define(CHUNK, 65536).

-spec run() -> no_return().
run() ->
    Io = #{read_file => fun file:read_file/1,
           read_stdin => fun read_stdin/0,
           out => fun(Data) -> io:put_chars(standard_io, Data) end,
           err => fun(Data) -> io:put_chars(standard_error, Data) end},
    halt(textstat_runner:run(init:get_plain_arguments(), Io)).

read_stdin() ->
    ok = io:setopts(standard_io, [binary]),
    read_chunks([]).

read_chunks(Acc) ->
    case io:get_chars(standard_io, "", ?CHUNK) of
        eof -> iolist_to_binary(lists:reverse(Acc));
        {error, _Reason} -> iolist_to_binary(lists:reverse(Acc));
        Data -> read_chunks([Data | Acc])
    end.
