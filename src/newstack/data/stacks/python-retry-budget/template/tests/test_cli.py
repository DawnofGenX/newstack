import json
from datetime import UTC

import pytest

from {{ package_name }} import cli as subject

START = 1_772_000_000 - (1_772_000_000 % 60)


def write(tmp_path, rows, name="traffic.jsonl"):
    path = tmp_path / name
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
    return path


@pytest.fixture()
def outage(tmp_path):
    rows = [{"at": START + index * 60, "good": 100, "bad": 0} for index in range(60)]
    rows += [{"at": START + (60 + index) * 60, "good": 0, "bad": 100} for index in range(5)]
    return str(write(tmp_path, rows))


def test_a_report_that_fires_exits_one(outage, capsys):
    assert subject.main(["report", "--events", outage, "--window", "1h"]) == subject.EXIT_BREACH
    printed = capsys.readouterr()
    assert "PAGE" in printed.out
    assert "budget" in printed.out


def test_a_report_that_is_clean_exits_zero(outage, capsys):
    code = subject.main(
        ["report", "--events", outage, "--window", "30m", "--now", _iso(START + 30 * 60)]
    )
    assert code == subject.EXIT_OK
    assert "0.00x" in capsys.readouterr().out


def test_json_mode_prints_the_shape(outage, capsys):
    subject.main(["report", "--events", outage, "--window", "1h", "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert payload["firing"] is True
    assert payload["verdicts"][0]["firing"] is True


def test_a_target_that_is_not_a_percentage_exits_two(outage, capsys):
    assert subject.main(["report", "--events", outage, "--target", "99,9"]) == subject.EXIT_UNUSABLE
    assert "not a percentage" in capsys.readouterr().err


def test_a_missing_events_file_exits_two(tmp_path, capsys):
    assert (
        subject.main(["report", "--events", str(tmp_path / "nope.jsonl")]) == subject.EXIT_UNUSABLE
    )
    assert "cannot read" in capsys.readouterr().err


def test_an_unaligned_bucket_exits_two(tmp_path, capsys):
    path = write(tmp_path, [{"at": START + 30, "good": 1, "bad": 0}])
    assert subject.main(["report", "--events", str(path)]) == subject.EXIT_UNUSABLE
    assert "not aligned" in capsys.readouterr().err


def test_a_now_without_an_offset_is_refused(outage, capsys):
    assert (
        subject.main(["report", "--events", outage, "--now", "2026-03-08T00:00:00"])
        == subject.EXIT_UNUSABLE
    )
    assert "no offset" in capsys.readouterr().err


def test_the_demo_is_as_advertised(capsys):
    assert subject.main(["demo"]) == subject.EXIT_OK
    assert "0 not as advertised" in capsys.readouterr().out


def test_the_demo_json_payload_is_green(capsys):
    assert subject.main(["demo", "--json"]) == subject.EXIT_OK
    assert json.loads(capsys.readouterr().out)["ok"] is True


def test_the_selftest_passes(capsys):
    assert subject.main(["selftest"]) == subject.EXIT_OK
    assert "0 failed" in capsys.readouterr().out


def test_version_and_help(capsys):
    with pytest.raises(SystemExit) as raised:
        subject.main(["--version"])
    assert raised.value.code == 0
    assert "0.1.0" in capsys.readouterr().out
    with pytest.raises(SystemExit) as raised:
        subject.main(["report", "--help"])
    assert raised.value.code == 0
    assert "--target" in capsys.readouterr().out


def _iso(seconds):
    from datetime import datetime

    return f"{datetime.fromtimestamp(seconds, tz=UTC):%Y-%m-%dT%H:%M:%SZ}"
