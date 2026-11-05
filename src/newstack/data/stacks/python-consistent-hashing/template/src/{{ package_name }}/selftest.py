"""Check the ring's promises against the ring, not against its documentation."""

from __future__ import annotations

import io
from contextlib import redirect_stderr, redirect_stdout

from .audit import AuditError, histogram, mod_map, moved, only_from, percentage, summary
from .cli import EXIT_BREACH, EXIT_OK, EXIT_UNUSABLE, main
from .demo import KEYS, NODES, load_table, ring_with
from .hashing import hash64, mod_slot, virtual_node_key
from .ring import Point, Ring, RingError

CHECKS: list[tuple[str, bool, str]] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    CHECKS.append((name, bool(condition), detail))


def refuses(name: str, kind: type[BaseException], call, needle: str = "") -> None:
    try:
        call()
    except kind as error:
        check(name, needle in str(error), f"message: {error}")
    except BaseException as error:  # a wrong exception type is a failure
        check(name, False, f"raised {type(error).__name__}, expected {kind.__name__}")
    else:
        check(name, False, "nothing was raised")


def quiet(argv: list[str]) -> tuple[int, str]:
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = main(argv)
    return code, out.getvalue()


def run() -> int:
    CHECKS.clear()

    # -- hashing --------------------------------------------------------------------
    check("hash64 is stable", hash64("user:00001") == hash64("user:00001"))
    check("hash64 separates neighbours", hash64("user:00001") != hash64("user:00002"))
    check("hash64 fits 64 bits", 0 <= hash64("x") < 1 << 64)
    check(
        "virtual node keys do not collide",
        virtual_node_key("a1", 2) != virtual_node_key("a", 12),
        f"{virtual_node_key('a1', 2)} vs {virtual_node_key('a', 12)}",
    )
    check("mod_slot stays in range", all(0 <= mod_slot(key, 7) < 7 for key in KEYS[:100]))
    refuses("mod_slot refuses zero slots", ValueError, lambda: mod_slot("k", 0))

    # -- ring -----------------------------------------------------------------------
    ring = ring_with(NODES)
    check("points = vnodes x weight", len(ring.points) == len(NODES) * ring.vnodes)
    check("points are sorted", ring.points == sorted(ring.points))
    check(
        "every key lands on a node",
        all(ring.get(key) in NODES for key in KEYS[:200]),
    )
    check(
        "owner agrees with get",
        all(ring.owner(key).node == ring.get(key) for key in KEYS[:200]),
    )
    loads = ring.loads(KEYS)
    check("every node carries keys", all(load > 0 for load in loads.values()), str(loads))
    check("loads add up", sum(loads.values()) == len(KEYS))
    check("shares add to one", abs(sum(ring.shares(KEYS).values()) - 1.0) < 1e-9)
    check("imbalance is finite", ring.imbalance(KEYS) != float("inf"))
    check("imbalance of no keys is infinite", ring_with(NODES).imbalance([]) == float("inf"))
    refuses("an empty ring refuses lookups", RingError, lambda: Ring().get("k"))
    refuses("a duplicate node is refused", RingError, lambda: ring.add("alpha"))
    refuses("a weight below one is refused", RingError, lambda: Ring().add("a", weight=0))
    refuses("removing an unknown node is refused", RingError, lambda: ring.remove("zulu"))
    refuses("vnodes below one is refused", RingError, lambda: Ring(vnodes=0))

    forward = ring_with(NODES).mapping(KEYS[:300])
    backward = Ring(vnodes=160)
    for node in reversed(NODES):
        backward.add(node)
    check("insertion order does not change the mapping", forward == backward.mapping(KEYS[:300]))

    first, last = ring.points[0], ring.points[-1]
    beyond = next(
        key
        for number in range(200_000)
        for key in (f"probe:{number}",)
        if hash64(key) > last.position
    )
    check(
        "a key past the last point wraps to the first node",
        ring.get(beyond) == first.node,
        f"{beyond} -> {ring.get(beyond)}",
    )
    check(
        "Point text is fixed width",
        len(Point(5, "a").text()) == len(Point(10**19, "a").text()),
        f"{len(Point(5, 'a').text())} vs {len(Point(10**19, 'a').text())}",
    )
    check("arc loads cover the ring", sum(ring.arc_loads().values()) == 1 << 64)
    check(
        "more points make the arcs even",
        ring_with(NODES, vnodes=160).arc_imbalance() < ring_with(NODES, vnodes=1).arc_imbalance(),
    )
    refuses("an empty ring has no arcs", RingError, lambda: Ring().arc_loads())

    # -- movement -------------------------------------------------------------------
    bigger = ring_with([*NODES, "foxtrot"])
    changes = moved(ring.mapping(KEYS), bigger.mapping(KEYS))
    check("the new node takes a share of keys", len(changes) > 0)
    check(
        "every moved key moved onto the new node",
        all(change.after == "foxtrot" for change in changes),
    )
    check(
        "the ring moved about one share, not everything",
        len(changes) < len(KEYS) * 0.32,
        f"{len(changes)} of {len(KEYS)}",
    )
    removed_changes = moved(bigger.mapping(KEYS), ring.mapping(KEYS))
    check("removal moves only the removed node's keys", only_from(removed_changes, "foxtrot"))
    smaller = ring_with(NODES[:4])
    check(
        "shrinking moves only the departing node's keys",
        only_from(moved(ring.mapping(KEYS), smaller.mapping(KEYS)), "echo"),
    )
    naive = moved(mod_map(KEYS, NODES), mod_map(KEYS, [*NODES, "foxtrot"]))
    check(
        "modulo moves far more than a ring",
        len(naive) > 4 * len(changes),
        f"modulo {len(naive)} vs ring {len(changes)}",
    )
    same = ring.mapping(KEYS[:10])
    check("summary names the count", "of" in summary(same, same))
    check("percentage of nothing is zero", percentage(0, 0) == 0.0)
    refuses(
        "comparing different key sets is refused",
        AuditError,
        lambda: moved({"a": "x"}, {"b": "x"}),
    )
    refuses("mod_map needs nodes", AuditError, lambda: mod_map(["a"], []))
    check("histogram is sorted by node", list(histogram({"a": "y", "b": "x"})) == ["x", "y"])

    # -- shape ----------------------------------------------------------------------
    coarse = ring_with(NODES, vnodes=1)
    check(
        "virtual nodes improve the split",
        ring.imbalance(KEYS) < coarse.imbalance(KEYS),
        f"{ring.imbalance(KEYS):.2f} vs {coarse.imbalance(KEYS):.2f}",
    )
    weighted = Ring(vnodes=200)
    weighted.add("small")
    weighted.add("big", weight=3)
    shares = weighted.shares(KEYS)
    ratio = shares["big"] / shares["small"]
    check("weights set the share", 2.4 < ratio < 3.6, f"ratio {ratio:.2f}")
    check("weighted points count", len(weighted.points) == 800)
    check("load_table has a line per node", len(load_table(ring, KEYS).splitlines()) == len(NODES))

    # -- cli ------------------------------------------------------------------------
    code, out = quiet(["map", "--nodes", "a,b,c", "--keys", "500"])
    check("map exits 0", code == EXIT_OK, f"code {code}")
    check("map prints the imbalance", "imbalance" in out)
    code, out = quiet(["move", "--nodes", "a,b,c", "--add", "d", "--keys", "2000"])
    check("move exits 0 inside the limit", code == EXIT_OK, f"code {code}")
    check("move says what modulo would do", "modulo" in out)
    code, _ = quiet(
        ["move", "--nodes", "a,b,c", "--add", "d", "--keys", "2000", "--max-moved", "1"]
    )
    check("move gates on the movement", code == EXIT_BREACH, f"code {code}")
    code, _ = quiet(["move", "--nodes", "a,b,c", "--add", "a", "--keys", "10"])
    check("move refuses an existing node", code == EXIT_UNUSABLE, f"code {code}")
    code, _ = quiet(["ring", "--key", "user:00001", "--nodes", "a,b,c"])
    check("ring exits 0", code == EXIT_OK)
    code, _ = quiet(["balance", "--nodes", "a,b,c", "--keys", "500", "--max-imbalance", "1.0"])
    check("balance gates on uneven splits", code == EXIT_BREACH, f"code {code}")
    code, _ = quiet(["map", "--nodes", "a,a", "--keys", "10"])
    check("map refuses duplicate nodes", code == EXIT_UNUSABLE, f"code {code}")
    code, _ = quiet(["map", "--nodes", "a", "--keys", "0"])
    check("map refuses zero keys", code == EXIT_UNUSABLE, f"code {code}")

    passed = sum(1 for _, held, _ in CHECKS if held)
    for name, held, detail in CHECKS:
        if not held:
            print(f"FAIL {name}: {detail}")
    print(f"selftest: {passed} of {len(CHECKS)} checks passed")
    return 0 if passed == len(CHECKS) else 1
