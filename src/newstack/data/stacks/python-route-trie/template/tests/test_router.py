import pytest

from {{ package_name }} import pattern as patterns
from {{ package_name }} import router as subject


def table():
    router = subject.Router()
    router.add("GET", "/", name="root")
    router.add("GET", "/users/me", name="me")
    router.add("GET", "/users/{id}", name="user")
    router.add("GET", "/users/{id}/posts", name="posts")
    router.add("POST", "/users/{id}/posts", name="create")
    router.add("DELETE", "/users/{id}", name="drop")
    router.add("GET", "/files/{name}", name="file")
    router.add("GET", "/files/*rest", name="tree")
    return router


def test_a_literal_beats_a_parameter():
    router = table()
    assert router.match("GET", "/users/me").route.name == "me"
    assert router.match("GET", "/users/7").route.name == "user"


def test_a_parameter_binds_the_segment_it_consumed():
    resolved = table().match("GET", "/users/7/posts")
    assert resolved.route.name == "posts"
    assert resolved.param("id") == "7"


def test_a_parameter_beats_a_catch_all():
    router = table()
    assert router.match("GET", "/files/a.txt").route.name == "file"
    assert router.match("GET", "/files/2026/11/a.txt").route.name == "tree"


def test_the_catch_all_keeps_the_rest_of_the_path():
    assert table().match("GET", "/files/2026/11/a.txt").param("rest") == "2026/11/a.txt"


def test_a_dead_branch_is_abandoned():
    router = subject.Router()
    router.add("GET", "/a/b/d")
    router.add("GET", "/a/{x}/c")
    resolved = router.match("GET", "/a/b/c")
    assert resolved.matched
    assert resolved.route.pattern.text == "/a/{x}/c"
    assert resolved.param("x") == "b"


def test_the_first_divergence_decides():
    router = subject.Router()
    router.add("GET", "/a/{x}/c")
    router.add("GET", "/a/b/{y}")
    assert router.match("GET", "/a/b/c").route.pattern.text == "/a/b/{y}"
    assert router.match("GET", "/a/z/c").route.pattern.text == "/a/{x}/c"


def test_a_wrong_method_is_not_a_miss():
    resolved = table().match("PUT", "/users/7/posts")
    assert resolved.kind == subject.NOT_ALLOWED
    assert resolved.allow == ("GET", "POST")
    assert "another method" in resolved.reason


def test_a_missing_path_is_a_miss_with_a_reason():
    resolved = table().match("GET", "/users/7/comments")
    assert resolved.kind == subject.NO_MATCH
    assert resolved.allow == ()
    assert resolved.reason


def test_the_root_matches_and_binds_nothing():
    resolved = table().match("GET", "/")
    assert resolved.route.name == "root"
    assert resolved.params == ()


def test_a_second_route_on_one_shape_is_refused():
    router = table()
    with pytest.raises(subject.RouterError) as caught:
        router.add("GET", "/users/{other}")
    assert "already registered" in str(caught.value)


def test_two_routes_may_differ_only_by_method():
    assert table().match("POST", "/users/7/posts").route.method == "POST"


def test_an_unknown_method_is_refused():
    with pytest.raises(subject.RouterError):
        table().add("TRACE", "/x")
    with pytest.raises(subject.RouterError):
        table().match("TRACE", "/")


def test_a_request_path_with_a_trailing_slash_is_refused():
    with pytest.raises(patterns.PatternError):
        table().match("GET", "/users/")


def test_the_route_list_is_sorted_and_complete():
    router = table()
    texts = [route.pattern.text for route in router.routes]
    assert len(texts) == 8
    assert texts == sorted(texts)


def test_lines_describe_each_route():
    lines = table().lines()
    assert len(lines) == 8
    assert any("/users/me" in line and "GET" in line for line in lines)


def test_a_resolution_serialises():
    payload = table().match("GET", "/users/7").as_dict()
    assert payload["kind"] == "match"
    assert payload["route"] == "GET /users/{id}"
    assert payload["params"] == {"id": "7"}


def test_an_unnamed_route_has_an_empty_name():
    router = subject.Router()
    router.add("GET", "/x")
    assert router.routes[0].name == ""
