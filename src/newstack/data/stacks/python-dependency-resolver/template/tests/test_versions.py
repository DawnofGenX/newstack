from {{ package_name }} import versions as subject


def test_parses_the_three_numbers():
    version = subject.parse("1.2.3")
    assert (version.major, version.minor, version.patch) == (1, 2, 3)
    assert version.prerelease == ()
    assert version.text == "1.2.3"


def test_the_specifications_own_ordering_example():
    order = [
        "1.0.0-alpha",
        "1.0.0-alpha.1",
        "1.0.0-alpha.beta",
        "1.0.0-beta",
        "1.0.0-beta.2",
        "1.0.0-beta.11",
        "1.0.0-rc.1",
        "1.0.0",
    ]
    parsed = [subject.parse(text) for text in order]
    assert parsed == sorted(parsed)
    assert parsed == sorted(parsed, reverse=True)[::-1]


def test_numeric_identifiers_compare_as_numbers():
    assert subject.parse("1.0.0-beta.11") > subject.parse("1.0.0-beta.2")


def test_a_release_outranks_its_own_prerelease():
    assert subject.parse("1.0.0") > subject.parse("1.0.0-rc.9")


def test_build_metadata_is_kept_but_never_compared():
    left = subject.parse("1.0.0+build.1")
    right = subject.parse("1.0.0+build.2")
    assert left == right
    assert not left < right
    assert not right < left
    assert left.text == "1.0.0+build.1"


def test_leading_zero_in_a_numeric_identifier_is_refused():
    try:
        subject.parse("1.0.0-01")
    except subject.VersionError as error:
        assert "leading zero" in str(error)
    else:
        raise AssertionError("1.0.0-01 should not parse")


def test_a_missing_patch_is_not_a_version():
    try:
        subject.parse("1.2")
    except subject.VersionError as error:
        assert "MAJOR.MINOR.PATCH" in str(error)
    else:
        raise AssertionError("1.2 should not parse")


def test_try_parse_returns_none_instead_of_raising():
    assert subject.try_parse("nope") is None
    assert subject.try_parse("2.0.0") == subject.parse("2.0.0")
