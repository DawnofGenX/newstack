import json

import pytest

from {{ package_name }} import index as index_module
from {{ package_name }} import lockfile as subject
from {{ package_name }} import resolver, versions

DIAMOND = {
    "web": {"2.0.0": {"shared": "^1.2.0"}, "2.1.0": {"shared": "^2.0.0"}},
    "shared": {"1.2.0": {}, "1.4.0": {}, "2.0.0": {}},
}


def build():
    return index_module.parse_index({"packages": DIAMOND})


def test_render_is_sorted_and_ends_with_a_newline():
    resolution = resolver.resolve(build(), {"web": "^2.0.0"})
    text = subject.render(resolution)
    assert text.endswith("\n")
    assert text.index('"shared"') < text.index('"web"')
    assert json.loads(text)["version"] == 1


def test_a_lock_round_trips_through_disk(tmp_path):
    resolution = resolver.resolve(build(), {"web": "^2.0.0"})
    path = subject.write(tmp_path / "deps.lock.json", resolution)
    lock = subject.read(path)
    assert {name: version.text for name, version in lock.packages.items()} == {
        "shared": "2.0.0",
        "web": "2.1.0",
    }


def test_a_future_format_is_refused():
    with pytest.raises(subject.LockError) as caught:
        subject.parse_lock({"version": 99, "packages": {"web": "1.0.0"}})
    assert "refusing to guess" in str(caught.value)


def test_an_empty_lock_is_refused():
    with pytest.raises(subject.LockError):
        subject.parse_lock({"version": 1, "packages": {}})


def test_locked_but_unneeded_is_drift():
    lock = subject.Lock({"web": versions.parse("2.0.0"), "gone": versions.parse("1.0.0")})
    drift = subject.audit(build(), lock, {"web": "^2.0.0"})
    assert "gone" in [entry.package for entry in drift]
    assert "nothing needs it" in drift[0].line()


def test_a_locked_version_the_requirements_exclude_is_drift():
    lock = subject.Lock({"web": versions.parse("1.0.0")})
    lines = {
        entry.package: entry.line() for entry in subject.audit(build(), lock, {"web": "^2.0.0"})
    }
    assert "locked at 1.0.0, but the requirements select 2.1.0" in lines["web"]
    assert "missing from the lock" in lines["shared"]


def test_a_current_lock_is_not_drift_even_when_a_newer_version_exists():
    lock = subject.Lock({"web": versions.parse("2.0.0"), "shared": versions.parse("1.4.0")})
    assert subject.audit(build(), lock, {"web": "^2.0.0"}) == []


def test_changed_lists_only_the_differences():
    before = subject.Lock({"web": versions.parse("2.0.0"), "gone": versions.parse("1.0.0")})
    after = resolver.resolve(build(), {"web": "^2.0.0"})
    lines = subject.changed(before, after)
    assert "  - gone 1.0.0" in lines
    assert "  + shared 2.0.0" in lines
    assert "  ~ web 2.0.0 -> 2.1.0" in lines
