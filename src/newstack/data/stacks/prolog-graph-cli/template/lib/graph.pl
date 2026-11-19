
:- module(graph_cli, [run/4, shortest_path/6, parse_graph/3]).

run(Args, Out, Err, Code) :-
    (   Args = ["--help"]
    ->  usage(Text),
        call(Out, Text),
        Code = 0
    ;   Args = ["-h"]
    ->  usage(Text),
        call(Out, Text),
        Code = 0
    ;   Args = [Graph, Start, End]
    ->  (   parse_graph(Graph, Edges, Nodes)
        ->  (   shortest_path(Edges, Nodes, Start, End, Dist, Path)
            ->  atomic_list_concat(Path, ' ', PathStr),
                format(string(Text), "distance: ~w~npath: ~w~n", [Dist, PathStr]),
                call(Out, Text),
                Code = 0
            ;   format(string(Text), "no path from ~w to ~w~n", [Start, End]),
                call(Err, Text),
                Code = 1
            )
        ;   format(string(Text), "error: cannot read graph '~w'~n", [Graph]),
            call(Err, Text),
            Code = 1
        )
    ;   usage(Text),
        call(Err, Text),
        Code = 2
    ).

usage(Text) :-
    format(string(Text),
           "Usage: graph-cli GRAPH START END~nShortest path in a directed weighted graph.~n",
           []).

%% Parse graph file: lines "u v w", comments with #, blank lines.
parse_graph(Path, Edges, Nodes) :-
    catch(read_file_to_string(Path, Content, []), _, fail),
    split_string(Content, "\n", "\r", RawLines),
    parse_lines(RawLines, Edges, NodeSet),
    sort(NodeSet, Nodes).

parse_lines([], [], []).
parse_lines([Line|Rest], Edges, Nodes) :-
    (   parse_line(Line, U, V, W)
    ->  Edges = [edge(U,V,W)|EdgesRest],
        Nodes = [U,V|NodesRest]
    ;   Edges = EdgesRest,
        Nodes = NodesRest
    ),
    parse_lines(Rest, EdgesRest, NodesRest).

parse_line(Line, U, V, W) :-
    split_string(Line, " \t", " \t", Parts),
    (   Parts = [_,_,_]
    ->  [US,VS,WS] = Parts,
        \+ sub_string(US, 0, 1, _, "#"),
        number_string(W, WS),
        U = US, V = VS
    ;   fail
    ).

%% Bellman-Ford shortest path.
shortest_path(Edges, Nodes, Start, End, Dist, Path) :-
    member(Start, Nodes),
    member(End, Nodes),
    init_dist(Nodes, Start, Dist0),
    init_prev(Nodes, Prev0),
    length(Nodes, V),
    relax_all(Edges, Nodes, V, Dist0, Prev0, DistF, PrevF),
    get_dist(DistF, End, D),
    D < 1000000000,
    reconstruct(PrevF, End, Start, Path),
    Dist = D.

init_dist([], _, []).
init_dist([N|Ns], Start, [N-D|Rest]) :-
    (   N == Start -> D = 0 ; D = 1000000000 ),
    init_dist(Ns, Start, Rest).

init_prev([], []).
init_prev([N|Ns], [N-none|Rest]) :-
    init_prev(Ns, Rest).

relax_all(_, _, 1, Dist, Prev, Dist, Prev) :- !.
relax_all(Edges, Nodes, K, Dist0, Prev0, DistF, PrevF) :-
    relax_edges_once(Edges, Dist0, Prev0, Dist1, Prev1),
    K1 is K - 1,
    relax_all(Edges, Nodes, K1, Dist1, Prev1, DistF, PrevF).

relax_edges_once([], Dist, Prev, Dist, Prev).
relax_edges_once([edge(U,V,W)|Es], Dist0, Prev0, DistF, PrevF) :-
    get_dist(Dist0, U, DU),
    get_dist(Dist0, V, DV),
    (   DU < 1000000000,
        Alt is DU + W,
        Alt < DV
    ->  set_dist(Dist0, V, Alt, Dist1),
        set_prev(Prev0, V, U, Prev1)
    ;   Dist1 = Dist0,
        Prev1 = Prev0
    ),
    relax_edges_once(Es, Dist1, Prev1, DistF, PrevF).

get_dist([N-D|_], N, D) :- !.
get_dist([_|Rest], N, D) :- get_dist(Rest, N, D).

set_dist([N-_|Rest], N, D, [N-D|Rest]) :- !.
set_dist([X|Rest], N, D, [X|Rest2]) :- set_dist(Rest, N, D, Rest2).

set_prev([N-_|Rest], N, P, [N-P|Rest]) :- !.
set_prev([X|Rest], N, P, [X|Rest2]) :- set_prev(Rest, N, P, Rest2).

reconstruct(_, Node, Start, [Start]) :- Node == Start, !.
reconstruct(Prev, Node, Start, Path) :-
    get_prev(Prev, Node, P),
    P \== none,
    reconstruct(Prev, P, Start, Rest),
    append(Rest, [Node], Path).

get_prev([N-P|_], N, P) :- !.
get_prev([_|Rest], N, P) :- get_prev(Rest, N, P).
