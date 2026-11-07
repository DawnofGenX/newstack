"""The matrix: the table the walker answers, every pair at once.

The rule this walker keeps, and the marker the detector looks for:
the table is the walker's table, pair for pair. Seeds sit first -
every node owes itself zero, every arrow sits at its weight - then
one triple loop lets every node speak as a stepping stone until no
stepping stone shortens anything. Weights are nonneg and the graph
is a digraph, so the table lands exactly where the per-node walk
lands: equal costs where the walker walks, silence where it does
not, and one more sweep changes nothing.

distances(graph) answers the table, worst_hop(graph) answers the
most distant reachable pair. An unreached ordered pair is omitted,
never spoken as infinity: the table says only what the arrows walk.
"""

from __future__ import annotations

from .graph import Graph

INFINITE = float("inf")


class TableError(ValueError):
    """A table that drifts from the walk, or a graph it refuses."""

    __slots__ = ()


def _matrix_of(graph: Graph) -> tuple:
    """The seeds: nodes in order, costs by index, diagonals at zero.

    A node owes itself zero before any arrow speaks, and every arrow
    sits at its weight; every other cell rests at infinity until a
    stepping stone moves it. Skip the zero seeds and the table stops
    being a walk - a node can no longer stand still on itself.
    """
    nodes = graph.nodes()
    room = len(nodes)
    place = {node: index for index, node in enumerate(nodes)}
    costs = [[INFINITE] * room for _ in range(room)]
    for index in range(room):
        costs[index][index] = 0
    for (source, target), weight in graph.edges():
        costs[place[source]][place[target]] = weight
    return nodes, place, costs


def _relaxed(graph: Graph) -> tuple:
    """The seeds walked to rest: every node, every stepping stone."""
    nodes, _place, costs = _matrix_of(graph)
    room = len(nodes)
    for step in range(room):
        for source in range(room):
            for target in range(room):
                if costs[source][step] + costs[step][target] < costs[source][target]:
                    costs[source][target] = costs[source][step] + costs[step][target]
    return nodes, costs


def distances(graph: Graph) -> dict:
    """The all-pairs table: (source, target) -> cost, ordered pairs.

    The diagonal is zero - every node stands on itself - and every
    reachable ordered pair carries its least cost. A pair the arrows
    never carries is omitted: the table speaks only what a walk can
    walk, and the walker omits what it cannot reach.
    """
    nodes, costs = _relaxed(graph)
    table: dict = {}
    for low, source in enumerate(nodes):
        for high, target in enumerate(nodes):
            if costs[low][high] != INFINITE:
                table[(source, target)] = costs[low][high]
    return dict(sorted(table.items()))


def worst_hop(graph: Graph) -> tuple:
    """The most distant reachable pair: (source, target, cost).

    The honest answer over the reachable table only: the dearthest
    cost among the pairs the arrows carry, ties answered by the
    lowest pair. A graph whose arrows carry no pair between distinct
    nodes has no distance to answer and says so.
    """
    table = distances(graph)
    hops = [(source, target, cost)
            for (source, target), cost in table.items() if source != target]
    if not hops:
        raise TableError("no hop between distinct nodes: nothing is distant")
    return max(hops, key=lambda hop: (hop[2], -hop[0], -hop[1]))


def audit(graph: Graph, table: dict) -> list:
    """Name every way a table drifts from the walk; empty holds.

    The walker's pairs and the table's pairs are the same pairs at
    the same costs, and every node sits at zero on itself. The deep
    promise - one more sweep changes nothing - rides the selftest.
    """
    from .oracle import distance_table

    breaks: list = []
    walked = distance_table(graph)
    if set(walked) != set(table):
        breaks.append("the table's pairs drift from the walker's pairs")
    for hop, cost in walked.items():
        if table.get(hop) != cost:
            breaks.append(f"{hop} costs {table.get(hop)!r}, the walk says {cost}")
    for node in graph.nodes():
        if table.get((node, node)) != 0:
            breaks.append(f"{node} does not stand at zero on itself")
    return breaks


def restated(table: dict) -> dict:
    """One more relaxation sweep over the table: pairs stay or move.

    The shipped table must rest: a sweep over the walker's own pairs
    hands back the same pairs at the same costs, the triangle
    inequality kept for every triple the table ships.
    """
    rest: dict = dict(table)
    for head, onward in sorted(table.items()):
        for tail, before in sorted(table.items()):
            if tail[1] == head[0]:
                joined = (tail[0], head[1])
                total = before + onward
                if joined not in rest or total < rest[joined]:
                    rest[joined] = total
    return dict(sorted(rest.items()))
