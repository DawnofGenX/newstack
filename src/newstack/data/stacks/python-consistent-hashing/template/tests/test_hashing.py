from {{ package_name }} import hashing as subject


def test_hash64_is_stable_across_calls() -> None:
    assert subject.hash64("user:00001") == subject.hash64("user:00001")


def test_hash64_separates_similar_text() -> None:
    assert subject.hash64("user:00001") != subject.hash64("user:00002")


def test_hash64_fits_in_64_bits() -> None:
    assert all(0 <= subject.hash64(text) < subject.WIDTH for text in ("", "a", "user:99999"))


def test_hash64_ignores_process_salt() -> None:
    # The value is baked in: hash() would change per interpreter and per restart.
    assert subject.hash64("alpha") == 5982700193828047002


def test_virtual_node_keys_do_not_collide_across_node_names() -> None:
    assert subject.virtual_node_key("a1", 2) != subject.virtual_node_key("a", 12)


def test_mod_slot_stays_in_range() -> None:
    assert all(0 <= subject.mod_slot(f"k{n}", 5) < 5 for n in range(200))


def test_mod_slot_refuses_zero_slots() -> None:
    try:
        subject.mod_slot("k", 0)
    except ValueError as error:
        assert "at least 1" in str(error)
    else:
        raise AssertionError("mod_slot accepted zero slots")
