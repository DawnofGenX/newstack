import json

from {{ package_name }} import cli

DATA = "data/dev.jsonl"
GOOD = "data/predictions.good.jsonl"
BAD = "data/predictions.bad.jsonl"


def run(capsys, *argv):
    status = cli.main(list(argv))
    out, err = capsys.readouterr()
    return status, out, err


def test_run_prints_the_score_and_the_answer_count(capsys):
    status, out, err = run(capsys, "run", "--data", DATA, "--predictions", GOOD)
    assert status == 0
    assert err == ""
    assert "metric    token_f1" in out
    assert "answered  4/4" in out


def test_run_writes_a_record_with_the_run_id_it_was_given(capsys, tmp_path):
    out_path = tmp_path / "run.json"
    argv = ("run", "--data", DATA, "--predictions", BAD, "--out", str(out_path), "--run-id", "v2")
    status, out, _err = run(capsys, *argv)
    assert status == 0
    record = json.loads(out_path.read_text())
    assert record["run_id"] == "v2"
    assert record["answered"] == 3
    assert record["missing"] == ["word-4"]
    assert f"record    {out_path}" in out


def test_the_default_run_id_is_the_predictions_file_stem(capsys, tmp_path):
    out_path = tmp_path / "run.json"
    run(capsys, "run", "--data", DATA, "--predictions", GOOD, "--out", str(out_path))
    assert json.loads(out_path.read_text())["run_id"] == "predictions.good"


def test_a_regression_exits_one_and_names_the_id(capsys, tmp_path):
    good = tmp_path / "good.json"
    bad = tmp_path / "bad.json"
    run(capsys, "run", "--data", DATA, "--predictions", GOOD, "--out", str(good))
    run(capsys, "run", "--data", DATA, "--predictions", BAD, "--out", str(bad))
    status, out, _err = run(capsys, "compare", "--baseline", str(good), "--candidate", str(bad))
    assert status == 1
    assert "regressed 4" in out
    assert "cap-1" in out


def test_an_improvement_exits_zero(capsys, tmp_path):
    good = tmp_path / "good.json"
    bad = tmp_path / "bad.json"
    run(capsys, "run", "--data", DATA, "--predictions", GOOD, "--out", str(good))
    run(capsys, "run", "--data", DATA, "--predictions", BAD, "--out", str(bad))
    status, out, _err = run(capsys, "compare", "--baseline", str(bad), "--candidate", str(good))
    assert status == 0
    assert "regressed 0" in out
    assert "delta     +" in out


def test_a_malformed_prediction_file_is_a_usage_error_not_a_traceback(capsys):
    malformed = "data/predictions.malformed.jsonl"
    status, out, err = run(capsys, "run", "--data", DATA, "--predictions", malformed)
    assert status == 2
    assert out == ""
    assert "duplicate id 'cap-1'" in err


def test_an_unknown_metric_is_a_usage_error(capsys):
    argv = ("run", "--data", DATA, "--predictions", GOOD, "--metric", "bleu")
    status, _out, err = run(capsys, *argv)
    assert status == 2
    assert "unknown metric" in err


def test_a_missing_data_file_says_cannot_read(capsys):
    status, _out, err = run(capsys, "run", "--data", "data/nope.jsonl", "--predictions", GOOD)
    assert status == 2
    assert "cannot read" in err
