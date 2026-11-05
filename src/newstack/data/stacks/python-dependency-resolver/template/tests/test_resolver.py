import pytest

from {{ package_name }} import index as index_module
from {{ package_name }} import resolver as subject
from {{ package_name }} import versions


def build(packages):
    return index_module.parse_index({"packages": packages})


DIAMOND = {
    "web": {
        "2.0.0": {"shared": "^1.2.0"},
        "2.1.0": {"shared": "^2.0.0"},
        "2.1.1": {"shared": "^2.0.0"},
    },
    "cli": {"1.0.0": {"shared": "^1.0.0"}, "1.1.0": {"shared": "^1.0.0"}},
    "shared": {"1.2.0": {}, "1.4.0": {}, "2.0.0": {}, "3.0.0-rc.1": {}},
}


def test_the_greedy_choice_is_abandoned_for_one_that_works():
    resolution = subject.resolve(build(DIAMOND), {"web": "^2.0.0", "cli": "^1.0.0"})
    assert resolution.version("web").text == "2.0.0"
    assert resolution.version("shared").text == "1.4.0"
    assert resolution.version("cli").text == "1.1.0"


def test_one_version_per_package_is_a_hard_rule():
    with pytest.raises(subject.ResolveError) as caught:
        subject.resolve(build(DIAMOND), {"web": "^2.1.0", "cli": "^1.0.0"})
    body = str(caught.value)
    assert "no resolution exists" in body
    assert "shared ^2.0.0" in body
    assert "^1.0.0" in body


def test_a_conflict_records_who_asked():
    with pytest.raises(subject.ResolveError) as caught:
        subject.resolve(build(DIAMOND), {"web": "^2.1.0", "cli": "^1.0.0"})
    assert any("was already chosen for" in item for item in caught.value.conflicts)


def test_root_order_does_not_change_the_answer():
    index = build(DIAMOND)
    one = subject.resolve(index, {"web": "^2.0.0", "cli": "^1.0.0"})
    two = subject.resolve(index, {"cli": "^1.0.0", "web": "^2.0.0"})
    assert one.as_dict()["packages"] == two.as_dict()["packages"]


def test_a_locked_version_is_preferred_when_it_still_fits():
    index = build(DIAMOND)
    locked = {"web": versions.parse("2.0.0"), "shared": versions.parse("1.2.0")}
    resolution = subject.resolve(index, {"web": "^2.0.0"}, locked=locked)
    assert resolution.version("web").text == "2.0.0"
    assert resolution.version("shared").text == "1.2.0"


def test_a_locked_version_that_does_not_fit_is_not_used():
    index = build(DIAMOND)
    locked = {"shared": versions.parse("1.2.0")}
    resolution = subject.resolve(index, {"shared": "^2.0.0"}, locked=locked)
    assert resolution.version("shared").text == "2.0.0"


def test_why_lists_every_requirement_known_at_the_end():
    resolution = subject.resolve(build(DIAMOND), {"web": "^2.0.0", "cli": "^1.0.0"})
    asked = "\n".join(resolution.why("shared"))
    assert "web@2.0.0 needs shared ^1.2.0" in asked
    assert "cli@1.1.0 needs shared ^1.0.0" in asked


def test_an_unknown_root_is_an_input_error_not_a_conflict():
    with pytest.raises(subject.ResolveError) as caught:
        subject.resolve(build(DIAMOND), {"nope": "^1.0.0"})
    assert "not published" in str(caught.value)


def test_a_cycle_terminates():
    index = build(
        {
            "left": {"1.0.0": {"right": "^1.0.0"}},
            "right": {"1.0.0": {"left": "^1.0.0"}},
        }
    )
    resolution = subject.resolve(index, {"left": "^1.0.0"})
    assert resolution.as_dict()["packages"] == {"left": "1.0.0", "right": "1.0.0"}


def test_the_search_stops_at_its_budget():
    index = build(DIAMOND)
    with pytest.raises(subject.ResolveError) as caught:
        subject.resolve(index, {"web": "^2.0.0"}, limit=1)
    assert "gave up after exploring" in str(caught.value)
