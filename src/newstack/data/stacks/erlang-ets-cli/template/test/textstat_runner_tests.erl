-module(textstat_runner_tests).
-include_lib("eunit/include/eunit.hrl").

program() -> list_to_binary(textstat_runner:program()).

%% Messages instead of channels: the runner's whole IO surface is a map.
capture(Args, Files, Stdin) ->
    Self = self(),
    ReadFile = fun(Path) ->
                       case lists:keyfind(Path, 1, Files) of
                           {Path, Data} -> {ok, Data};
                           false -> {error, enoent}
                       end
               end,
    Io = #{read_file => ReadFile,
           read_stdin => fun() -> Stdin end,
           out => fun(Data) -> Self ! {out, iolist_to_binary(Data)}, ok end,
           err => fun(Data) -> Self ! {err, iolist_to_binary(Data)}, ok end},
    Code = textstat_runner:run(Args, Io),
    {Code, drain(out, []), drain(err, [])}.

drain(Tag, Acc) ->
    receive
        {Tag, Data} -> drain(Tag, [Data | Acc])
    after 0 ->
            iolist_to_binary(lists:reverse(Acc))
    end.

with_stdin_test_() ->
    [?_assertEqual({0, <<"3 -\n">>, <<>>}, capture(["-w"], [], <<"alpha beta\ngamma\n">>)),
     ?_assertEqual({0, <<" 2  3 17 -\n">>, <<>>}, capture([], [], <<"alpha beta\ngamma\n">>)),
     ?_assertEqual({0, <<"17 -\n">>, <<>>}, capture(["-c", "-"], [], <<"alpha beta\ngamma\n">>))].

two_files_share_one_width_test_() ->
    Files = [{"a.txt", <<"alpha beta\ngamma\n">>}, {"b.txt", <<"x\n">>}],
    Result = capture(["a.txt", "b.txt"], Files, <<>>),
    [?_assertEqual(0, element(1, Result)),
     ?_assertEqual(<<" 2  3 17 a.txt\n 1  1  2 b.txt\n 3  4 19 total\n">>, element(2, Result)),
     ?_assertEqual(<<>>, element(3, Result))].

one_figure_has_no_padding_test() ->
    Files = [{"a.txt", <<"alpha beta\ngamma\n">>}],
    {0, Out, <<>>} = capture(["-w", "a.txt"], Files, <<>>),
    ?assertEqual(<<"3 a.txt\n">>, Out).

an_unreadable_file_test_() ->
    Files = [{"a.txt", <<"alpha beta\ngamma\n">>}],
    Result = capture(["a.txt", "missing.txt"], Files, <<>>),
    [?_assertEqual(1, element(1, Result)),
     ?_assertEqual(<<"error: cannot open 'missing.txt'\n">>, element(3, Result)),
     ?_assertEqual(<<" 2  3 17 a.txt\n 2  3 17 total\n">>, element(2, Result))].

usage_error_test_() ->
    Result = capture(["--bogus"], [], <<>>),
    Expected = <<(program())/binary, ": unknown option: --bogus\n"
                 "Try '", (program())/binary, " --help' for more information.\n">>,
    [?_assertEqual(2, element(1, Result)),
     ?_assertEqual(Expected, element(3, Result)),
     ?_assertEqual(<<>>, element(2, Result))].

help_test_() ->
    Result = capture(["--help"], [], <<>>),
    Prefix = <<"usage: ", (program())/binary, " [-l] [-w] [-c] [FILE ...]\n">>,
    [?_assertEqual(0, element(1, Result)),
     ?_assertEqual(<<>>, element(3, Result)),
     ?_assertEqual(Prefix, binary:part(element(2, Result), 0, byte_size(Prefix)))].

version_test_() ->
    Result = capture(["--version"], [], <<>>),
    [?_assertEqual(0, element(1, Result)),
     ?_assertEqual(<<(program())/binary, " 0.1.0\n">>, element(2, Result))].
