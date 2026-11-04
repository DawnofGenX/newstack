from __future__ import annotations

import json

from newstack.cli import main


def test_list_text_lists_every_stack(capsys) -> None:
    assert main(["list"]) == 0
    out = capsys.readouterr().out
    for name in ("python-lib", "python-cli", "fastapi", "react-vite-ts", "node-express-ts"):
        assert name in out


def test_list_json_is_machine_readable(capsys) -> None:
    assert main(["list", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert len(payload) >= 6
    assert {"name", "title", "language", "blurb", "requires"} <= set(payload[0])


def test_version(capsys) -> None:
    assert main(["version"]) == 0
    assert capsys.readouterr().out.strip().count(".") == 2


def test_doctor_reports_toolchains(capsys) -> None:
    assert main(["doctor"]) == 0
    assert "stacks can be verified" in capsys.readouterr().out


def test_new_generates_project(tmp_path, capsys) -> None:
    dest = tmp_path / "mylib"
    code = main(["new", "python-lib", str(dest), "--name", "mylib", "-d", "Demo", "--no-git"])
    assert code == 0
    assert (dest / "pyproject.toml").is_file()
    assert (dest / "src/mylib/core.py").is_file()
    assert "mylib" in (dest / "README.md").read_text()
    assert 'name = "mylib"' in (dest / "pyproject.toml").read_text()
    assert "created" in capsys.readouterr().out


def test_new_json_output(tmp_path, capsys) -> None:
    dest = tmp_path / "api"
    code = main(["new", "fastapi", str(dest), "--no-git", "--json"])
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["stack"] == "fastapi"
    assert len(payload["files"]) >= 5
    assert payload["git"] is None


def test_new_dry_run_writes_nothing(tmp_path) -> None:
    dest = tmp_path / "ghost"
    assert main(["new", "python-cli", str(dest), "--dry-run"]) == 0
    assert not dest.exists()


def test_new_rejects_unknown_stack(tmp_path, capsys) -> None:
    assert main(["new", "nope", str(tmp_path / "x")]) == 1
    assert "unknown stack" in capsys.readouterr().err


def test_new_rejects_bad_project_name(tmp_path, capsys) -> None:
    assert main(["new", "python-lib", str(tmp_path / "x"), "--name", "has space"]) == 1
    assert "invalid project name" in capsys.readouterr().err


def test_new_refuses_to_overwrite(tmp_path, capsys) -> None:
    dest = tmp_path / "taken"
    dest.mkdir()
    (dest / "keep.txt").write_text("mine")
    assert main(["new", "python-lib", str(dest), "--no-git"]) == 1
    assert "not empty" in capsys.readouterr().err


def test_package_name_sanitises_awkward_names(tmp_path) -> None:
    leading_digit = tmp_path / "digit"
    assert main(["new", "python-lib", str(leading_digit), "--name", "2fast", "--no-git"]) == 0
    assert (leading_digit / "src/app_2fast").is_dir()

    reserved = tmp_path / "keyword"
    assert main(["new", "python-lib", str(reserved), "--name", "class", "--no-git"]) == 0
    assert (reserved / "src/class_app").is_dir()


def test_cabal_name_never_reads_as_a_version() -> None:
    from newstack.cli import _cabal_name

    # cabal parses `tool-2024` as package `tool` version `2024` and refuses the file.
    assert _cabal_name("tool-2024") == "tool-v2024"
    assert _cabal_name("my.tool_2") == "my-tool-v2"
    assert _cabal_name("tool2024") == "tool2024"
    assert _cabal_name("tool-v2") == "tool-v2"
    assert _cabal_name("2fast") == "2fast"


def test_class_name_is_a_pascal_case_identifier() -> None:
    from newstack.cli import _class_name

    assert _class_name("my-tool") == "MyTool"
    assert _class_name("my_tool") == "MyTool"
    assert _class_name("myTool") == "MyTool"
    assert _class_name("railsproj") == "Railsproj"
    assert _class_name("2fast") == "App2fast"
    assert _class_name("---") == "App"


def test_haskell_project_name_ending_in_a_number_still_renders_a_legal_package(tmp_path) -> None:
    dest = tmp_path / "hs"
    assert main(["new", "haskell-cli", str(dest), "--name", "tool-2024", "--no-git"]) == 0
    cabal = dest / "tool-v2024.cabal"
    assert cabal.is_file()
    text = cabal.read_text()
    assert "name:               tool-v2024" in text
    # the executable keeps the name the user typed
    assert "executable tool-2024" in text
    assert (dest / "bin/tool-2024").is_file()


def test_check_unknown_stack_errors(capsys) -> None:
    assert main(["check", "nope"]) == 1
    assert "unknown stack" in capsys.readouterr().err


def test_check_without_arguments_errors(capsys) -> None:
    assert main(["check"]) == 1
    assert "at least one stack" in capsys.readouterr().err


def test_generated_project_has_no_unresolved_placeholders(tmp_path) -> None:
    import re

    for stack in ("python-lib", "python-cli", "fastapi", "react-vite-ts", "node-express-ts"):
        dest = tmp_path / stack
        assert main(["new", stack, str(dest), "--no-git", "--json"]) == 0
        for path in dest.rglob("*"):
            if path.is_file():
                text = path.read_text(encoding="utf-8", errors="ignore")
                assert not re.search(r"(?<!\$)\{\{", text), f"{stack}:{path}"


def _half_built_stack(tmp_path, monkeypatch):
    root = tmp_path / "stacks"
    broken = root / "half-built"
    broken.mkdir(parents=True)
    (broken / "stack.json").write_text(
        '{"name": "half-built", "title": "Half", "language": "go", "blurb": "wip"}',
        encoding="utf-8",
    )
    monkeypatch.setenv("NEWSTACK_STACKS", str(root))
    return broken


def test_list_survives_a_half_built_stack(tmp_path, monkeypatch, capsys) -> None:
    _half_built_stack(tmp_path, monkeypatch)
    assert main(["list"]) == 0
    captured = capsys.readouterr()
    assert "half-built" in captured.err
    assert "missing template/" in captured.err
    assert "stacks available" in captured.out


def test_check_all_fails_on_an_unusable_stack_directory(tmp_path, monkeypatch, capsys) -> None:
    _half_built_stack(tmp_path, monkeypatch)

    class _Pass:
        ok = True
        seconds = 0.0
        outcomes: list = []
        directory = None

        def as_dict(self):
            return {}

    monkeypatch.setattr("newstack.cli.check_stack", lambda *a, **k: _Pass())
    monkeypatch.setattr("newstack.cli.missing_tools", lambda stack: [])

    assert main(["check", "--all"]) == 1
    out = capsys.readouterr().out
    assert "half-built" in out and "unusable" in out


def test_package_name_is_never_a_reserved_word() -> None:
    """`package static;` and `package class` do not compile in the languages we ship."""
    import keyword

    from newstack.cli import JAVA_RESERVED, _package_name

    for name in ("class", "static", "package", "import", "interface", "void", "try", "my-app"):
        slug = _package_name(name)
        assert slug not in keyword.kwlist, f"{name!r} rendered as Python keyword {slug!r}"
        assert slug not in JAVA_RESERVED, f"{name!r} rendered as Java keyword {slug!r}"
        assert slug.isidentifier() or "_" in slug


def test_java_stack_builds_a_legal_package_from_a_reserved_name(tmp_path) -> None:
    """Prove it end to end: the generated sources must not declare `package static;`."""
    from newstack.cli import build_context_for_check
    from newstack.registry import get_stack
    from newstack.render import generate

    stack = get_stack("java-maven-cli")
    generate(stack.template_dir, tmp_path, build_context_for_check(stack, "static"))

    sources = list((tmp_path / "src").rglob("*.java"))
    assert sources, "the java stack generated no sources"
    for source in sources:
        text = source.read_text(encoding="utf-8")
        assert "package static;" not in text, f"{source} declares an illegal package"
        assert "package static_app;" in text, f"{source} does not use the sanitised package"
    assert (tmp_path / "src/main/java/static_app").is_dir()
