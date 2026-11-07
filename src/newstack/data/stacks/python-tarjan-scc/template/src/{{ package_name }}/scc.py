"""The walker: one pass, and the partition answers.

The rule this walker keeps:
two nodes share a component only when each reaches the other.
And the answer it hands back is the oracle's partition, component
for component, on every graph the corpora hold. The walk carries
an index, a lowlink, and a stack; the lowlink keeps the child's
lowlink across a back edge, and the pop boundary is the node's own
index, not its parent's. Break either and the partition drifts
from the oracle.

partition(graph) answers the components, condense(graph) answers
the DAG they fold to. The promise is checked, never assumed:
selftest and the suites compare every walk against the oracle.
"""

from __future__ import annotations

from .graph import Graph


class PartitionError(ValueError):
    """A graph the walker refuses to walk."""

    __slots__ = ()


def partition(graph: Graph) -> tuple:
    """The components, one pass deep, the oracle's answer exactly.

    Tarjan's walk over an explicit stack: every node gets an index
    and a lowlink, a back edge hands the child's lowlink up, and a
    root pops its whole subtree the moment its lowlink returns to
    its own index. Components are frozensets, ordered by smallest
    label - the same partition the reachability oracle answers.
    """
    index: dict = {}
    low: dict = {}
    stack: list = []
    on_stack: set = set()
    counter = 0
    groups: list = []
    for root in graph.nodes():
        if root in index:
            continue
        index[root] = low[root] = counter
        counter += 1
        stack.append(root)
        on_stack.add(root)
        work = [(root, iter(graph.successors(root)))]
        while work:
            node, children = work[-1]
            advanced = False
            for child in children:
                if child not in index:
                    index[child] = low[child] = counter
                    counter += 1
                    stack.append(child)
                    on_stack.add(child)
                    work.append((child, iter(graph.successors(child))))
                    advanced = True
                    break
                if child in on_stack and low[child] < low[node]:
                    low[node] = low[child]
            if advanced:
                continue
            work.pop()
            if low[node] >= index[node]:
                cut = len(stack) - 1
                while stack[cut] != node:
                    cut -= 1
                popped = frozenset(stack[cut:])
                for member in popped:
                    on_stack.discard(member)
                del stack[cut:]
                groups.append(popped)
            if work:
                parent = work[-1][0]
                if low[node] < low[parent]:
                    low[parent] = low[node]
    return tuple(sorted(groups, key=min))


def strong_components(graph: Graph) -> list:
    """The partition, as a list: the library's published spelling."""
    return list(partition(graph))


def audit(graph: Graph, groups: tuple) -> list:
    """Name every way a partition fails the seat promise; empty holds.

    Every node lands in exactly one component: the seats add up,
    every node has a seat, and no component repeats a name. The
    equal-oracle tests carry the deeper promise - this audit is
    the cheap shape check the walker owes its own answer.
    """
    breaks: list = []
    nodes = set(graph.nodes())
    seats = [member for group in groups for member in group]
    if len(seats) != len(nodes):
        breaks.append(f"{len(seats)} seats for {len(nodes)} nodes")
    if set(seats) != nodes:
        breaks.append("a node missed its component")
    if len({id(group) for group in groups}) != len(groups):
        breaks.append("two components share a body")
    return breaks


def condense(graph: Graph) -> Graph:
    """The DAG the components fold to, each answered by its head.

    A component is named by its smallest label; every edge between
    components survives, every edge inside one dissolves. The
    answer is acyclic - cycle.has_cycle walks it and finds none.
    """
    groups = partition(graph)
    home: dict = {}
    dag = Graph()
    for group in groups:
        head = min(group)
        for member in group:
            home[member] = head
        dag.add_node(head)
    for source, target in graph.edges():
        if home[source] != home[target]:
            dag.add_edge(home[source], home[target])
    return dag
