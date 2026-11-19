-module(textstat_options_tests).
-include_lib("eunit/include/eunit.hrl").

field(Args, Key) ->
    maps:get(Key, textstat_options:parse(Args)).

no_arguments_wants_every_figure_test() ->
    ?assertEqual([l, w, c], field([], figures)),
    ?assertEqual([], field([], files)).

one_flag_test() ->
    ?assertEqual([l], field(["-l"], figures)).

a_cluster_test() ->
    ?assertEqual([l, w], field(["-lw"], figures)).

a_repeated_flag_is_not_repeated_test() ->
    ?assertEqual([l], field(["-ll"], figures)).

the_long_form_test() ->
    ?assertEqual([c], field(["--bytes"], figures)).

flag_then_file_test() ->
    ?assertEqual(["notes.txt"], field(["-c", "notes.txt"], files)),
    ?assertEqual([c], field(["-c", "notes.txt"], figures)).

dash_is_stdin_test() ->
    ?assertEqual(["-"], field(["-"], files)).

double_dash_ends_the_options_test() ->
    ?assertEqual(["-l"], field(["--", "-l"], files)),
    ?assertEqual([l, w, c], field(["--", "-l"], figures)).

help_test() ->
    ?assertEqual(help, field(["--help"], status)),
    ?assertEqual(help, field(["-h"], status)).

help_stops_the_parse_test() ->
    ?assertEqual([], field(["--help", "-l"], figures)).

version_test() ->
    ?assertEqual(version, field(["--version"], status)),
    ?assertEqual(version, field(["-V"], status)).

unknown_long_option_test() ->
    ?assertEqual(usage_error, field(["--bogus"], status)),
    ?assertEqual("unknown option: --bogus", field(["--bogus"], message)).

unknown_short_option_test() ->
    ?assertEqual(usage_error, field(["-x"], status)),
    ?assertEqual("unknown option: -x", field(["-x"], message)).

a_cluster_with_a_bad_letter_test() ->
    ?assertEqual(usage_error, field(["-lx"], status)),
    ?assertEqual("unknown option: -x", field(["-lx"], message)).

usage_mentions_the_program_name_test() ->
    ?assert(string:find(textstat_options:usage("prog"), "usage: prog [-l]") =/= nomatch).
