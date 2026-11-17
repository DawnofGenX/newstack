from {{ package_name }}.fts import add_document, connect, ensure_schema, escape_query, search


def corpus(conn):
    ensure_schema(conn)
    add_document(conn, 1, "apple pie recipe", "bake apples with sugar and cinnamon")
    add_document(conn, 2, "banana bread", "mash bananas and bake")
    add_document(conn, 3, "apple cake", "apples and flour and sugar")


def test_ranking_order():
    conn = connect(":memory:")
    corpus(conn)
    res = search(conn, "apple")
    ids = [r["id"] for r in res]
    assert 1 in ids and 3 in ids
    assert 2 not in ids
    # bm25 lower is better; ensure score ordering
    scores = [r["score"] for r in res]
    assert scores == sorted(scores)
    conn.close()


def test_snippet_highlighting():
    conn = connect(":memory:")
    corpus(conn)
    res = search(conn, "apple")
    assert any("[" in r["snippet"] and "]" in r["snippet"] for r in res)
    conn.close()


def test_query_escaping():
    conn = connect(":memory:")
    corpus(conn)
    # should not raise
    res = search(conn, 'apple "bad syntax')
    assert isinstance(res, list)
    conn.close()


def test_escape_produces_quoted_terms():
    assert escape_query("a b") == '"a" "b"'