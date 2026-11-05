import json
from pathlib import Path

from {{ package_name }} import cli

FIXTURE = "fixtures/policy.json"


def run(capsys, *arguments):
    code = cli.main(list(arguments))
    captured = capsys.readouterr()
    return code, captured.out + captured.err


def test_an_allowed_request_exits_zero(capsys):
    code, out = run(
        capsys,
        "decide",
        "--policy",
        FIXTURE,
        "--subject",
        "alice",
        "--action",
        "docs:write",
        "--resource",
        "project:acme/doc:1",
    )
    assert code == 0
    assert "ALLOW" in out


def test_a_denied_request_exits_one(capsys):
    code, out = run(
        capsys,
        "decide",
        "--policy",
        FIXTURE,
        "--subject",
        "mallory",
        "--action",
        "docs:read",
        "--resource",
        "project:acme/doc:1",
    )
    assert code == 1
    assert "DENY" in out


def test_attributes_are_accepted_as_pairs(tmp_path, capsys):
    policy = json.loads(Path(FIXTURE).read_text(encoding="utf-8"))
    path = tmp_path / "policy.json"
    path.write_text(json.dumps(policy), encoding="utf-8")
    code, out = run(
        capsys,
        "decide",
        "--policy",
        str(path),
        "--subject",
        "carol",
        "--action",
        "comments:create",
        "--resource",
        "project:acme/doc:7",
        "--subject-attr",
        "id=carol",
        "--resource-attr",
        "owner=carol",
    )
    assert code == 0, out


def test_json_output_is_parseable(capsys):
    code, out = run(
        capsys,
        "decide",
        "--policy",
        FIXTURE,
        "--subject",
        "alice",
        "--action",
        "docs:read",
        "--resource",
        "project:acme/doc:1",
        "--json",
    )
    assert code == 0
    assert json.loads(out)["allowed"] is True


def test_a_missing_flag_is_a_usage_error(capsys):
    code, out = run(capsys, "decide", "--policy", FIXTURE, "--subject", "alice")
    assert code == 2
    assert "required" in out


def test_an_unknown_command_is_a_usage_error(capsys):
    code, out = run(capsys, "explain-everything")
    assert code == 2
    assert "unknown command" in out


def test_a_malformed_attribute_is_refused(capsys):
    code, out = run(
        capsys,
        "decide",
        "--policy",
        FIXTURE,
        "--subject",
        "alice",
        "--action",
        "docs:read",
        "--resource",
        "project:acme/doc:1",
        "--subject-attr",
        "noequals",
    )
    assert code == 2
    assert "KEY=VALUE" in out


def test_check_passes_the_shipped_policy(capsys):
    code, out = run(capsys, "check", "--policy", FIXTURE)
    assert code == 0, out
    assert "no findings" in out


def test_check_reports_a_role_nobody_holds(tmp_path, capsys):
    policy = json.loads(Path(FIXTURE).read_text(encoding="utf-8"))
    policy["roles"]["ghost"] = {}
    path = tmp_path / "policy.json"
    path.write_text(json.dumps(policy), encoding="utf-8")
    code, out = run(capsys, "check", "--policy", str(path))
    assert code == 1
    assert "never assigned" in out


def test_check_reports_an_allow_that_can_never_win(tmp_path, capsys):
    payload = {
        "roles": {"v": {}},
        "assignments": [{"subject": "a", "role": "v"}],
        "rules": [
            {
                "id": "allow-it",
                "effect": "allow",
                "action": "docs:read",
                "resource": "project:**",
                "roles": ["v"],
            },
            {
                "id": "deny-it",
                "effect": "deny",
                "action": "docs:read",
                "resource": "project:**",
                "subjects": ["*"],
            },
        ],
    }
    path = tmp_path / "policy.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    code, out = run(capsys, "check", "--policy", str(path))
    assert code == 1
    assert "can never win" in out


def test_check_points_at_a_one_segment_wildcard(tmp_path, capsys):
    payload = {
        "roles": {"v": {}},
        "assignments": [{"subject": "a", "role": "v"}],
        "rules": [
            {
                "id": "shallow",
                "effect": "allow",
                "action": "docs:read",
                "resource": "project:*",
                "roles": ["v"],
            },
            {
                "id": "deep",
                "effect": "allow",
                "action": "docs:read",
                "resource": "project:acme/doc:1",
                "roles": ["v"],
            },
        ],
    }
    path = tmp_path / "policy.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    code, out = run(capsys, "check", "--policy", str(path))
    assert code == 1
    assert "**" in out


def test_a_missing_policy_file_is_a_usage_error(capsys):
    code, out = run(
        capsys,
        "decide",
        "--policy",
        "/nonexistent/policy.json",
        "--subject",
        "a",
        "--action",
        "b",
        "--resource",
        "c",
    )
    assert code == 2
    assert "cannot read" in out


def test_version_and_help(capsys):
    assert run(capsys, "--version")[0] == 0
    code, out = run(capsys, "--help")
    assert code == 0
    assert "usage:" in out
