from __future__ import annotations

import pytest

from newstack.render import TemplateError, generate, render_string


def test_render_string_substitutes_variables() -> None:
    assert render_string("hi {{ name }}", {"name": "ada"}) == "hi ada"
    assert render_string("{{a}}{{ a }}{{  a  }}", {"a": "x"}) == "xxx"


def test_render_string_supports_dotted_keys() -> None:
    assert render_string("{{ meta.year }}", {"meta": {"year": 2026}}) == "2026"


def test_render_string_keeps_github_expressions() -> None:
    text = "python: ${{ matrix.python-version }} and ${{ env.FOO }}"
    assert render_string(text, {"matrix": {}, "env": {}}) == text


def test_render_string_escapes_literal_braces() -> None:
    assert render_string("{{! not_a_var }}", {}) == "{{ not_a_var }}"


def test_render_string_records_missing_variables() -> None:
    missing: list[str] = []
    out = render_string("{{ known }} {{ unknown }}", {"known": "1"}, missing=missing)
    assert out == "1 {{ unknown }}"
    assert missing == ["unknown"]


def test_render_string_leaves_double_brace_object_literals_alone() -> None:
    assert render_string("style={{ color: 'red' }}", {}) == "style={{ color: 'red' }}"


def _template(tmp_path, files: dict[str, str]):
    root = tmp_path / "tmpl"
    for rel, content in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return root


def test_generate_renders_paths_and_content(tmp_path) -> None:
    tmpl = _template(
        tmp_path,
        {
            "README.md": "# {{ title }}\n",
            "src/{{ package_name }}/__init__.py": 'NAME = "{{ project_name }}"\n',
        },
    )
    dest = tmp_path / "out"
    context = {"title": "Hello", "package_name": "hello", "project_name": "hello"}
    result = generate(tmpl, dest, context)

    assert result.count == 2
    assert (dest / "src/hello/__init__.py").read_text() == 'NAME = "hello"\n'
    assert (dest / "README.md").read_text() == "# Hello\n"


def test_generate_rejects_unknown_variables(tmp_path) -> None:
    tmpl = _template(tmp_path, {"a.txt": "{{ nope }}"})
    with pytest.raises(TemplateError, match="nope"):
        generate(tmpl, tmp_path / "out", {})


def test_generate_refuses_non_empty_destination(tmp_path) -> None:
    tmpl = _template(tmp_path, {"a.txt": "ok"})
    dest = tmp_path / "out"
    dest.mkdir()
    (dest / "keep.txt").write_text("mine")
    with pytest.raises(TemplateError, match="not empty"):
        generate(tmpl, dest, {})
    assert (dest / "keep.txt").read_text() == "mine"


def test_generate_force_overwrites_existing_files(tmp_path) -> None:
    tmpl = _template(tmp_path, {"a.txt": "new", "b.txt": "b"})
    dest = tmp_path / "out"
    dest.mkdir()
    (dest / "a.txt").write_text("old")
    result = generate(tmpl, dest, {}, force=True)
    assert (dest / "a.txt").read_text() == "new"
    assert result.overwritten == ["a.txt"]
    assert (dest / "b.txt").read_text() == "b"


def test_generate_dry_run_writes_nothing(tmp_path) -> None:
    tmpl = _template(tmp_path, {"a.txt": "x"})
    dest = tmp_path / "out"
    result = generate(tmpl, dest, {}, dry_run=True)
    assert result.count == 1
    assert not dest.exists()


def test_generate_refuses_path_escape(tmp_path) -> None:
    tmpl = _template(tmp_path, {"{{ evil }}.txt": "x"})
    with pytest.raises(TemplateError, match="outside the project"):
        generate(tmpl, tmp_path / "out", {"evil": "../../etc/passwd"})


def test_generate_copies_binary_files(tmp_path) -> None:
    tmpl = tmp_path / "tmpl"
    tmpl.mkdir()
    (tmpl / "logo.bin").write_bytes(bytes(range(256)))
    dest = tmp_path / "out"
    generate(tmpl, dest, {})
    assert (dest / "logo.bin").read_bytes() == bytes(range(256))
