:- module(server, [main/0]).

:- initialization(main, main).

:- use_module(library(http/thread_httpd)).
:- use_module(library(http/http_dispatch)).
:- use_module(library(http/http_json)).
:- use_module(library(http/http_client)).
:- use_module(library(uri)).
:- use_module('contract.pl').

:- http_handler(root(.), handle_request, [prefix]).

%! handle_request(+Request) is det.
%
%  The only place that knows about the network: read the request, call the
%  contract, write the reply.
handle_request(Request) :-
    option(method(Verb), Request),
    upcase_atom(Verb, Method),
    option(path(PathAtom), Request),
    atom_string(PathAtom, Path),
    (   option(search(Pairs), Request)
    ->  uri_query_components(Query, Pairs)
    ;   Query = ""
    ),
    read_body(Request, Body),
    contract:route(Method, Path, Query, Body, reply(Status, Dict)),
    reply_json_dict(Dict, [status(Status)]).

read_body(Request, Body) :-
    % A request stream only ends where Content-Length says it does, so ask
    % for exactly that many characters; a GET without a body reads nothing
    % instead of blocking on the socket.
    (   option(content_length(Length), Request),
        Length > 0
    ->  option(input(Stream), Request),
        catch(read_string(Stream, Length, Text), _, fail),
        (   string(Text)
        ->  Body = Text
        ;   Body = ""
        )
    ;   Body = ""
    ).

%! main is det.
%
%  PORT picks the listening port (default 8080); the socket is bound to
%  loopback only.
main :-
    (   catch(getenv('PORT', PortAtom), _, fail)
    ->  atom_number(PortAtom, Port)
    ;   Port = 8080
    ),
    http_server(http_dispatch, [port(Port), ip('127.0.0.1')]),
    format("listening on http://127.0.0.1:~w~n", [Port]),
    thread_get_message(_).
