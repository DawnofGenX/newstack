%! run-tests is det.
%
%  The whole contract without a socket: the counting table first, then one
%  case per branch of the route table. Run with `swipl tests/run-tests.pl`.
:- initialization(main, main).

%  Load the modules next to this script, wherever it is run from.
:- prolog_load_context(directory, Here),
   directory_file_path(Here, '../src/counts.pl', Counts),
   directory_file_path(Here, '../src/contract.pl', Contract),
   use_module(Counts),
   use_module(Contract).

main :-
    nb_setval(checks, 0),
    nb_setval(failures, 0),
    forall(member(Check, [counts_cases, contract_cases]), call(Check)),
    nb_getval(checks, Checks),
    nb_getval(failures, Failures),
    (   Failures =:= 0
    ->  format("~w checks passed~n", [Checks]),
        halt(0)
    ;   format("~w of ~w checks failed~n", [Failures, Checks]),
        halt(1)
    ).

check(Name, Goal) :-
    nb_getval(checks, Checks),
    Checks1 is Checks + 1,
    nb_setval(checks, Checks1),
    (   catch(Goal, Error, (print_message(error, Error), fail))
    ->  true
    ;   nb_getval(failures, Failures),
        Failures1 is Failures + 1,
        nb_setval(failures, Failures1),
        format("FAIL ~w~n", [Name])
    ).

counts_cases :-
    check("hello world", count_text("hello world\n", counts{lines: 1, words: 2, bytes: 12})),
    check("empty input", count_text("", counts{lines: 0, words: 0, bytes: 0})),
    check("blank lines are lines", count_text("\n\nx\n", counts{lines: 3, words: 1, bytes: 4})),
    check("whitespace without a word", count_text("  \t ", counts{lines: 0, words: 0, bytes: 4})),
    check("a word without a trailing newline", count_text("abc", counts{lines: 0, words: 1, bytes: 3})),
    check("utf-8 bytes are bytes, not characters",
          count_text("héllo wörld\n", counts{lines: 1, words: 2, bytes: 14})),
    check("multi-byte characters", count_text("🙂\n", counts{lines: 1, words: 1, bytes: 5})).

contract_cases :-
    check("health", route('GET', "/health", "", "", reply(200, _{status: "ok"}))),
    check("GET /stats counts the query",
          route('GET', "/stats", "text=hello%20world%0A", "",
                reply(200, _{text: "hello world\n", lines: 1, words: 2, bytes: 12}))),
    check("GET /stats decodes plus as space",
          route('GET', "/stats", "text=a+b", "", reply(200, _{text: "a b", lines: 0, words: 2, bytes: 3}))),
    check("GET /stats decodes an encoded ampersand",
          route('GET', "/stats", "text=a%26b", "", reply(200, _{text: "a&b", lines: 0, words: 1, bytes: 3}))),
    check("GET /stats with an empty text counts zeros",
          route('GET', "/stats", "text=", "", reply(200, _{text: "", lines: 0, words: 0, bytes: 0}))),
    check("GET /stats without text is 422",
          route('GET', "/stats", "", "", reply(422, _{error: "missing_text"}))),
    check("POST /stats counts the body",
          route('POST', "/stats", "", '{"text":"a b\nc\n"}',
                reply(200, _{text: "a b\nc\n", lines: 2, words: 3, bytes: 6}))),
    check("POST /stats with no text is 422",
          route('POST', "/stats", "", "{}", reply(422, _{error: "missing_text"}))),
    check("POST /stats with a non-string text is 422",
          route('POST', "/stats", "", '{"text":42}', reply(422, _{error: "missing_text"}))),
    check("POST /stats with a broken body is 422",
          route('POST', "/stats", "", "nope", reply(422, _{error: "invalid_json"}))),
    check("POST /stats with a json scalar is not an object",
          route('POST', "/stats", "", '"text"', reply(422, _{error: "invalid_json"}))),
    check("unknown route is a json 404 with the method and path",
          route('GET', "/nope", "", "",
                reply(404, _{error: "not_found", detail: "no route for GET /nope"}))),
    check("a known path with another method is 405",
          route('DELETE', "/health", "", "", reply(405, _{error: "method_not_allowed"}))),
    check("a known path with another method is 405 (post)",
          route('PUT', "/stats", "", "", reply(405, _{error: "method_not_allowed"}))).
