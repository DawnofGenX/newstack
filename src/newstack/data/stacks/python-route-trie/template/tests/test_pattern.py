import pytest

from {{ package_name }} import pattern as subject


def test_a_pattern_knows_its_segments():
    parsed = subject.parse_pattern("/users/{id}/posts")
    assert [segment.kind for segment in parsed.segments] == ["static", "param", "static"]
    assert parsed.params == ("id",)
    assert parsed.depth == 3
    assert parsed.shape() == "static param static"


def test_a_catch_all_is_named_and_last():
    parsed = subject.parse_pattern("/files/*rest")
    assert parsed.catchall == "rest"
    assert parsed.segments[-1].kind == "catchall"


def test_an_unnamed_catch_all_gets_a_name():
    assert subject.parse_pattern("/files/*").params == ("rest",)


def test_the_root_has_no_segments():
    parsed = subject.parse_pattern("/")
    assert parsed.segments == ()
    assert parsed.params == ()
    assert parsed.shape() == "(root)"


def test_a_pattern_renders_back_to_itself():
    for text in ("/", "/users", "/users/{id}", "/files/*rest", "/a/{x}/b/*rest"):
        assert subject.parse_pattern(text).render() == text


@pytest.mark.parametrize(
    ("text", "needle"),
    [
        ("users", "does not start with '/'"),
        ("", "cannot be empty"),
        ("/v{major}", "mixes a literal with a wildcard"),
        ("/a/{x}y", "mixes a literal with a wildcard"),
        ("/*all/end", "nothing can follow it"),
        ("/{id}/{id}", "names 'id' twice"),
        ("/a//b", "empty segment"),
        ("/a/", "trailing slash"),
        ("/{1id}", "not a parameter name"),
        ("/*1rest", "not a catch-all name"),
    ],
)
def test_a_pattern_that_could_be_read_two_ways_is_refused(text, needle):
    with pytest.raises(subject.PatternError) as caught:
        subject.parse_pattern(text)
    assert needle in str(caught.value)


def test_a_request_path_splits_the_same_way():
    assert subject.split_path("/a/b") == ("a", "b")
    assert subject.split_path("/") == ()


def test_a_trailing_slash_is_not_folded():
    with pytest.raises(subject.PatternError) as caught:
        subject.split_path("/users/")
    assert "trailing slash" in str(caught.value)


def test_split_path_refuses_a_relative_path():
    with pytest.raises(subject.PatternError):
        subject.split_path("users/1")


def test_a_literal_has_no_name():
    with pytest.raises(subject.PatternError):
        _ = subject.Segment("static", "users").name
