:- module(graph_test, [run/0]).
:- use_module('../lib/graph.pl').
:- use_module('harness.pl').

run :-
    harness:run_cases(graph_test,
      [direct_edge, two_hop, no_path, equal_start_end, weighted_choice]).

direct_edge :-
    Edges = [edge(a,b,5)],
    Nodes = [a,b],
    graph_cli:shortest_path(Edges, Nodes, a, b, D, P),
    harness:check_eq('direct dist', D, 5),
    harness:check_eq('direct path', P, [a,b]).

two_hop :-
    Edges = [edge(a,b,4), edge(a,c,2), edge(c,b,1)],
    Nodes = [a,b,c],
    graph_cli:shortest_path(Edges, Nodes, a, b, D, P),
    harness:check_eq('twohop dist', D, 3),
    harness:check_eq('twohop path', P, [a,c,b]).

no_path :-
    Edges = [edge(a,b,1)],
    Nodes = [a,b,c],
    \+ graph_cli:shortest_path(Edges, Nodes, a, c, _, _).

equal_start_end :-
    Edges = [edge(a,b,1)],
    Nodes = [a,b],
    graph_cli:shortest_path(Edges, Nodes, a, a, D, P),
    harness:check_eq('zero dist', D, 0),
    harness:check_eq('zero path', P, [a]).

weighted_choice :-
    Edges = [edge(s,a,1), edge(s,b,4), edge(a,t,2), edge(b,t,1)],
    Nodes = [s,a,b,t],
    graph_cli:shortest_path(Edges, Nodes, s, t, D, P),
    harness:check_eq('weighted dist', D, 3),
    harness:check_eq('weighted path', P, [s,a,t]).
