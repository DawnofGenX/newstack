:- module(contract, [route/5]).

:- use_module(library(http/json)).
:- use_module(library(uri)).
:- use_module('counts.pl').

%! route(+Method: atom, +Path: string, +Query: string, +Body: string,
%!       -Reply: reply(Status, Dict)) is det.
%
%  The whole route table as one pure predicate. No sockets, no request
%  object: a test can call this directly.
route(Method, Path, Query, Body, Reply) :-
    (   Method == 'GET', Path == "/health"
    ->  Reply = reply(200, _{status: "ok"})
    ;   Method == 'GET', Path == "/stats"
    ->  (   query_text(Query, Text)
        ->  stats_dict(Text, Dict), Reply = reply(200, Dict)
        ;   Reply = reply(422, _{error: "missing_text"})
        )
    ;   Method == 'POST', Path == "/stats"
    ->  body_text(Body, Parsed),
        (   Parsed = text(Text)
        ->  stats_dict(Text, Dict), Reply = reply(200, Dict)
        ;   Parsed == invalid
        ->  Reply = reply(422, _{error: "invalid_json"})
        ;   Reply = reply(422, _{error: "missing_text"})
        )
    ;   ( Path == "/health" ; Path == "/stats" )
    ->  Reply = reply(405, _{error: "method_not_allowed"})
    ;   format(string(Detail), "no route for ~w ~w", [Method, Path]),
        Reply = reply(404, _{error: "not_found", detail: Detail})
    ).

stats_dict(Text, Dict) :-
    counts:count_text(Text, counts{lines: Lines, words: Words, bytes: Bytes}),
    Dict = _{text: Text, lines: Lines, words: Words, bytes: Bytes}.

query_text(Query, Text) :-
    % uri_query_components/2 hands back atoms; the contract speaks strings.
    (   catch(uri_query_components(Query, Pairs), _, fail),
        memberchk(text=Value, Pairs)
    ->  atom_string(Value, Text)
    ;   fail
    ).

body_text(Body, Result) :-
    (   catch(atom_json_dict(Body, Dict, [value_string_as(string)]), _, fail)
    ->  (   is_dict(Dict)
        ->  (   catch((Text = Dict.text, string(Text)), _, fail)
            ->  Result = text(Text)
            ;   Result = missing
            )
        ;   Result = invalid
        )
    ;   Result = invalid
    ).
