import json

from {{ package_name }} import cli as subject


def _corpus(tmp_path) -> "object":
    base = "the quick brown fox jumps over the lazy dog and then goes home tonight"
    rows = [
        {"name": "a", "text": base},
        {"name": "b", "text": base},
        {"name": "c", "text": "a different sentence about weather, seasons and the sea"},
    ]
    path = tmp_path / "corpus.jsonl"
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    return path


def test_a_signature_prints_a_signature(capsys, tmp_path) -> None:
    text = tmp_path / "one.txt"
    text.write_text("the quick brown fox jumps over the lazy dog", encoding="utf-8")
    assert subject.main(["signature", "--text", str(text), "--width", "32"]) == 0
    assert "signature" in capsys.readouterr().out


def test_signature_json_reports_the_width(capsys) -> None:
    code = subject.main(["signature", "--string", "a b c d e f", "--width", "16", "--json"])
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["width"] == 16
    assert len(payload["signature"]) == 16


def test_identical_files_read_as_similar(capsys, tmp_path) -> None:
    text = "the quick brown fox jumps over the lazy dog and then goes home again"
    left, right = tmp_path / "l.txt", tmp_path / "r.txt"
    left.write_text(text, encoding="utf-8")
    right.write_text(text, encoding="utf-8")
    code = subject.main(["similar", "--left", str(left), "--right", str(right)])
    assert code == 0
    assert "similar" in capsys.readouterr().out


def test_unlike_files_exit_one(capsys, tmp_path) -> None:
    left, right = tmp_path / "l.txt", tmp_path / "r.txt"
    left.write_text("the quick brown fox jumps over the lazy dog tonight", encoding="utf-8")
    right.write_text("a different sentence about weather and the open sea", encoding="utf-8")
    assert subject.main(["similar", "--left", str(left), "--right", str(right)]) == 1
    assert "different" in capsys.readouterr().out


def test_dedupe_reports_the_cluster(capsys, tmp_path) -> None:
    code = subject.main(["dedupe", "--corpus", str(_corpus(tmp_path)), "--threshold", "0.5"])
    assert code == 0
    assert "cluster" in capsys.readouterr().out


def test_dedupe_can_fail_a_build(tmp_path) -> None:
    corpus = _corpus(tmp_path)
    assert subject.main([
        "dedupe", "--corpus", str(corpus), "--threshold", "0.5", "--fail-on-duplicates",
    ]) == 1


def test_a_missing_corpus_exits_two(capsys, tmp_path) -> None:
    assert subject.main(["candidates", "--corpus", str(tmp_path / "absent.jsonl")]) == 2
    assert "error" in capsys.readouterr().err


def test_bands_without_rows_exits_two(tmp_path) -> None:
    corpus = _corpus(tmp_path)
    assert subject.main(["candidates", "--corpus", str(corpus), "--bands", "8"]) == 2


def test_a_curve_prints_a_probability(capsys) -> None:
    assert subject.main(["curve", "--points", "5"]) == 0
    assert "probability" in capsys.readouterr().out


def test_the_parser_routes_every_command() -> None:
    parser = subject.build_parser()
    for command in ("signature", "similar", "candidates", "dedupe", "curve", "demo", "selftest"):
        parsed = parser.parse_args([command] + (
            ["--left", "a", "--right", "b"] if command == "similar" else []
        ) + (["--corpus", "c"] if command in ("candidates", "dedupe") else []))
        assert callable(parsed.handler)


def test_a_signature_without_text_exits_two(capsys) -> None:
    assert subject.main(["signature"]) == 2
    assert "error" in capsys.readouterr().err
