from {{ package_name }} import ring as subject

NODES = ["alpha", "bravo", "charlie"]
KEYS = [f"user:{number:04d}" for number in range(600)]


def build(nodes: list[str] = NODES, **kwargs) -> subject.Ring:
    ring = subject.Ring(**kwargs)
    for node in nodes:
        ring.add(node)
    return ring


def test_points_are_vnodes_times_weight() -> None:
    ring = subject.Ring(vnodes=10)
    ring.add("a")
    ring.add("b", weight=3)
    assert len(ring.points) == 40


def test_points_are_sorted() -> None:
    ring = build(vnodes=7)
    assert ring.points == sorted(ring.points)


def test_every_key_lands_on_a_node() -> None:
    ring = build()
    assert {ring.get(key) for key in KEYS} <= set(NODES)


def test_owner_matches_get() -> None:
    ring = build()
    assert all(ring.owner(key).node == ring.get(key) for key in KEYS)


def test_every_node_carries_some_keys() -> None:
    loads = build().loads(KEYS)
    assert set(loads) == set(NODES)
    assert all(count > 0 for count in loads.values())


def test_insertion_order_does_not_matter() -> None:
    forward = build().mapping(KEYS)
    backward = subject.Ring(vnodes=subject.DEFAULT_VNODES)
    for node in reversed(NODES):
        backward.add(node)
    assert forward == backward.mapping(KEYS)


def test_lookup_wraps_past_the_last_point() -> None:
    ring = build()
    last = max(point.position for point in ring.points)
    beyond = next(
        key
        for number in range(200_000)
        for key in (f"probe:{number}",)
        if subject.hash64(key) > last
    )
    assert ring.get(beyond) == ring.points[0].node


def test_empty_ring_refuses_lookups() -> None:
    try:
        subject.Ring().get("key")
    except subject.RingError as error:
        assert "empty" in str(error)
    else:
        raise AssertionError("an empty ring answered")


def test_adding_the_same_node_twice_is_refused() -> None:
    ring = build()
    try:
        ring.add("alpha")
    except subject.RingError as error:
        assert "already" in str(error)
    else:
        raise AssertionError("a duplicate node was accepted")


def test_weight_below_one_is_refused() -> None:
    try:
        subject.Ring().add("a", weight=0)
    except subject.RingError as error:
        assert "weight" in str(error)
    else:
        raise AssertionError("weight 0 was accepted")


def test_removing_an_unknown_node_is_refused() -> None:
    try:
        build().remove("zulu")
    except subject.RingError as error:
        assert "not on the ring" in str(error)
    else:
        raise AssertionError("an unknown node was removed")


def test_removal_moves_only_the_removed_nodes_keys() -> None:
    before = build([*NODES, "delta"]).mapping(KEYS)
    after = build().mapping(KEYS)
    assert {key for key in KEYS if before[key] != after[key]} == {
        key for key in KEYS if before[key] == "delta"
    }


def test_vnodes_even_out_the_load() -> None:
    coarse = build(vnodes=1).imbalance(KEYS)
    fine = build(vnodes=160).imbalance(KEYS)
    assert fine < coarse


def test_weights_set_the_share() -> None:
    ring = subject.Ring(vnodes=200)
    ring.add("small")
    ring.add("big", weight=3)
    shares = ring.shares(KEYS)
    assert 2.4 < shares["big"] / shares["small"] < 3.6


def test_shares_add_to_one() -> None:
    assert abs(sum(build().shares(KEYS).values()) - 1.0) < 1e-9


def test_arc_loads_cover_the_whole_ring() -> None:
    ring = build(vnodes=10)
    assert sum(ring.arc_loads().values()) == 1 << 64


def test_arc_imbalance_shrinks_with_more_points() -> None:
    assert build(vnodes=160).arc_imbalance() < build(vnodes=1).arc_imbalance()


def test_arc_loads_refuse_an_empty_ring() -> None:
    try:
        subject.Ring().arc_loads()
    except subject.RingError as error:
        assert "empty" in str(error)
    else:
        raise AssertionError("an empty ring reported arcs")


def test_point_text_is_fixed_width() -> None:
    assert len(subject.Point(7, "a").text()) == len(subject.Point(10**19, "a").text())
