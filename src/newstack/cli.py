"""Command line interface for newstack."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from . import __version__
from .adopt import apply_plan, detect_stacks, plan_adoption
from .registry import RegistryError, Stack, get_stack, load_catalog
from .render import TemplateError, generate
from .upgrade import (
    ADD,
    CONFLICT,
    ORPHAN,
    ORPHAN_EDITED,
    RECORD_NAME,
    UNCHANGED,
    UPDATE,
    apply_update,
    plan_update,
    read_record,
    sha256_bytes,
    write_record,
)
from .verify import check_stack, missing_tools

TOOLCHAIN_CHECKS = {
    "python3": "Python",
    "uv": "uv (Python package manager)",
    "git": "Git",
    "gh": "GitHub CLI",
    "node": "Node.js",
    "npm": "npm",
    "pnpm": "pnpm",
    "go": "Go",
    "cargo": "Rust / Cargo",
    "docker": "Docker",
}

PY_RESERVED = {
    "and", "as", "assert", "async", "await", "break", "class", "continue", "def", "del", "elif",
    "else", "except", "finally", "for", "from", "global", "if", "import", "in", "is", "lambda",
    "nonlocal", "not", "or", "pass", "raise", "return", "try", "while", "with", "yield",
}  # fmt: skip

NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


# --------------------------------------------------------------------------- helpers


# Reserved words in the languages that consume ``package_name``. A generated
# `package static;` (Java) or `package class` (Python) does not build, so the
# sanitiser has to know about both, not just Python's keyword list.
JAVA_RESERVED = frozenset({
    "abstract", "assert", "boolean", "break", "byte", "case",
    "catch", "char", "class", "const", "continue", "default",
    "do", "double", "else", "enum", "extends", "final",
    "finally", "float", "for", "goto", "if", "implements",
    "import", "instanceof", "int", "interface", "long", "native",
    "new", "package", "private", "protected", "public", "return",
    "short", "static", "strictfp", "super", "switch", "synchronized",
    "this", "throw", "throws", "transient", "try", "void",
    "volatile", "while", "true", "false", "null", "var",
    "record", "sealed", "permits", "yield",
})


def _package_name(name: str) -> str:
    slug = re.sub(r"[^0-9A-Za-z]+", "_", name).strip("_").lower()
    if not slug:
        slug = "app"
    if slug[0].isdigit():
        slug = f"app_{slug}"
    if slug in PY_RESERVED or slug in JAVA_RESERVED:
        slug = f"{slug}_app"
    return slug


def _npm_name(name: str) -> str:
    slug = re.sub(r"[^a-z0-9._-]+", "-", name.lower()).strip("-._")
    return slug or "app"


def _cabal_name(name: str) -> str:
    """A cabal package name where every hyphen-separated word contains a letter.

    Cabal reads ``tool-2024`` as the package ``tool`` at version ``2024`` and refuses
    to parse the file, so a numeric word is given a letter of its own: ``tool-v2024``.
    Executable names have no such rule, which is why the binary keeps ``npm_name``.
    """
    words = [word for word in re.sub(r"[^0-9a-z]+", "-", name.lower()).split("-") if word]
    words = [word if re.search(r"[a-z]", word) else f"v{word}" for word in words]
    return "-".join(words) or "app"


def _title(name: str) -> str:
    words = re.split(r"[-_.\s]+", name)
    return " ".join(word[:1].upper() + word[1:] for word in words if word)


def _git_config(key: str) -> str:
    try:
        value = subprocess.run(
            ["git", "config", "--get", key], capture_output=True, text=True, check=False
        ).stdout.strip()
    except OSError:
        return ""
    return value


class _SafeDict(dict):
    """format_map target that leaves unknown keys visible instead of raising."""

    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


def _format_step(step: str, context: dict, path: Path) -> str:
    return step.format_map(
        _SafeDict(
            path=path,
            project_name=context["project_name"],
            package_name=context["package_name"],
            npm_name=context["npm_name"],
        )
    )


def build_context(stack: Stack, destination: Path, args: argparse.Namespace) -> dict:
    project_name = args.name or destination.name
    author = args.author or _git_config("user.name") or "Your Name"
    email = args.email or _git_config("user.email") or "noreply@example.com"
    today = datetime.now(timezone.utc).date()
    return {
        "project_name": project_name,
        "package_name": _package_name(project_name),
        "npm_name": _npm_name(project_name),
        "cabal_name": _cabal_name(project_name),
        "title": _title(project_name),
        "description": args.description or stack.default_description,
        "author": author,
        "email": email,
        "year": today.year,
        "date": today.isoformat(),
        "stack": stack.name,
        "stack_title": stack.title,
        "newstack_version": __version__,
    }


def _count(number: int, word: str = "file") -> str:
    return f"{number} {word}" if number == 1 else f"{number} {word}s"


def _validate_name(name: str, what: str = "project name") -> None:
    if not name:
        raise TemplateError(f"{what} cannot be empty")
    if len(name) > 64:
        raise TemplateError(f"{what} is longer than 64 characters")
    if not NAME_RE.match(name):
        raise TemplateError(
            f"invalid {what} '{name}': use letters, digits, dots, dashes or underscores"
        )


def _run(cmd: list[str], cwd: Path) -> tuple[bool, str]:
    try:
        completed = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)
    except OSError as exc:
        return False, str(exc)
    if completed.returncode != 0:
        return False, (completed.stderr or completed.stdout).strip()
    return True, completed.stdout.strip()


# --------------------------------------------------------------------------- commands


def _write_generation_record(
    destination: Path, stack: Stack, context: dict, files: list[str]
) -> None:
    """Remember exactly what newstack wrote so ``update`` can merge safely later."""
    digests: dict[str, str] = {}
    for rel in files:
        try:
            digests[rel] = sha256_bytes((destination / rel).read_bytes())
        except OSError:
            continue
    write_record(destination, stack.name, context, digests)


def cmd_new(args: argparse.Namespace) -> int:
    stack = get_stack(args.stack)
    destination = Path(args.path).expanduser().resolve()
    context = build_context(stack, destination, args)
    _validate_name(context["project_name"])

    result = generate(
        stack.template_dir,
        destination,
        context,
        force=args.force,
        dry_run=args.dry_run,
    )

    report: dict = {
        "stack": stack.name,
        "path": str(destination),
        "dry_run": args.dry_run,
        "files": result.files,
        "overwritten": result.overwritten,
        "git": None,
        "github": None,
    }

    if not args.dry_run:
        _write_generation_record(destination, stack, context, result.files)

    if not args.dry_run and not args.no_git and shutil.which("git"):
        ok, out = _run(["git", "init", "-b", "main"], destination)
        if ok:
            _run(["git", "add", "-A"], destination)
            ok, out = _run(
                [
                    "git",
                    "-c",
                    f"user.name={context['author']}",
                    "-c",
                    f"user.email={context['email']}",
                    "commit",
                    "-m",
                    "Initial commit from newstack",
                ],
                destination,
            )
            report["git"] = {"initialized": True, "commit": ok, "detail": out}
        else:
            report["git"] = {"initialized": False, "detail": out}

    if args.github and not args.dry_run:
        slug = args.github if isinstance(args.github, str) else context["project_name"]
        if not shutil.which("gh"):
            raise TemplateError("--github needs the GitHub CLI (gh) on PATH")
        cmd = ["gh", "repo", "create", slug, "--source", ".", "--push"]
        cmd.append("--private" if args.private else "--public")
        ok, out = _run(cmd, destination)
        if not ok:
            raise TemplateError(f"gh repo create failed: {out}")
        ok, url = _run(["gh", "repo", "view", slug, "--json", "url", "--jq", ".url"], destination)
        report["github"] = url if ok else out

    if args.json:
        print(json.dumps(report, indent=2))
        return 0

    _print_new_report(stack, destination, context, result, report)
    return 0


def _print_new_report(
    stack: Stack, destination: Path, context: dict, result, report: dict
) -> None:
    print(f"\nnewstack {__version__}  ·  {stack.name}  →  {destination}\n")
    verb = "would create" if result.dry_run else "created"
    print(f"  {verb:<13} {result.count} files")
    for name in result.files:
        print(f"      {'+' if not result.dry_run else '·'} {name}")
    if result.overwritten:
        names = ", ".join(result.overwritten)
        print(f"  {'overwritten':<13} {len(result.overwritten)} existing files ({names})")
    git = report.get("git")
    if git and git.get("initialized") and git.get("commit"):
        print(f"  {'git':<13} initialised on main, first commit made")
    if report.get("github"):
        print(f"  {'github':<13} {report['github']}")
    if not result.dry_run:
        print(f"  {'record':<13} {RECORD_NAME} (newstack update re-applies template changes)")

    if stack.next_steps:
        print("\n  next:")
        for step in stack.next_steps:
            print(f"    {_format_step(step, context, destination)}")
    print()


def cmd_adopt(args: argparse.Namespace) -> int:
    root = Path(args.path).expanduser().resolve()
    if not root.is_dir():
        raise TemplateError(f"not a directory: {root}")

    if args.stack:
        stack = get_stack(args.stack)
        detected = False
    else:
        candidates = detect_stacks(root)
        if not candidates:
            raise TemplateError(
                "could not recognise this project's stack — pass --stack "
                "(see `newstack list`)"
            )
        if len(candidates) > 1:
            names = ", ".join(candidate.name for candidate in candidates)
            print(f"newstack: this directory matches more than one stack: {names}", file=sys.stderr)
            print("newstack: pass --stack <name> to choose one", file=sys.stderr)
            return 2
        stack = candidates[0]
        detected = True

    context = build_context(stack, root, args)
    plan = plan_adoption(
        stack, root, context, with_tests=args.with_tests, detected=detected
    )

    if not args.dry_run:
        apply_plan(plan)

    if args.json:
        payload = plan.as_dict()
        payload["dry_run"] = args.dry_run
        print(json.dumps(payload, indent=2))
        return 0

    _print_adopt_report(plan, context, dry_run=args.dry_run)
    return 0


def _print_adopt_report(plan, context: dict, *, dry_run: bool) -> None:
    print(f"\nnewstack {__version__}  ·  adopt  →  {plan.root}\n")
    how = "auto-detected" if plan.detected else "--stack"
    print(f"  {'stack':<12} {plan.stack.name} ({how})")
    verb = "would add" if dry_run else "added"
    print(f"  {verb:<12} {len(plan.add)} files")
    for item in plan.add:
        print(f"      + {item.rel}")
    if plan.keep:
        print(f"  {'kept':<12} {len(plan.keep)} existing files, left untouched")
        for rel in plan.keep:
            print(f"      = {rel}")
    if plan.manual:
        print(f"  {'manual':<12} {plan.manual[0]}")
        for extra in plan.manual[1:]:
            print(f"  {'':<12} {extra}")
    if not plan.add:
        print(f"  {'nothing':<12} the infrastructure files are already present")
    if not plan.tests_available and plan.stack.adopt_tests:
        print(f"  {'tests':<12} not copied — rerun with --with-tests if you want starter tests")
    if plan.stack.next_steps:
        print("\n  next:")
        print(f"    review the additions:  git -C {plan.root} status --short")
        print("    checks run on push:    the workflow above is the only thing that changed")
    print()


def cmd_update(args: argparse.Namespace) -> int:
    root = Path(args.path).expanduser().resolve()
    if not root.is_dir():
        raise TemplateError(f"not a directory: {root}")

    record = read_record(root)
    if args.stack:
        stack = get_stack(args.stack)
    elif record:
        stack = get_stack(record.stack)
    else:
        raise TemplateError(
            f"no {RECORD_NAME} in {root} — pass --stack <name> to say which "
            "template this project tracks (see `newstack list`)"
        )

    context = dict(record.context) if record else build_context(stack, root, args)
    if args.author:
        context["author"] = args.author
    if args.email:
        context["email"] = args.email
    if args.description is not None:
        context["description"] = args.description

    plan = plan_update(
        stack, root, record=record, context=context, force=args.force, prune=args.prune
    )

    applied = [] if args.dry_run else apply_update(plan)

    if args.json:
        payload = plan.as_dict()
        payload["dry_run"] = args.dry_run
        payload["applied"] = [action.rel for action in applied]
        print(json.dumps(payload, indent=2))
        return 0 if plan.ok else 1

    _print_update_report(plan, dry_run=args.dry_run)
    return 0 if plan.ok else 1


def _print_update_report(plan, *, dry_run: bool) -> None:
    print(f"\nnewstack {__version__}  ·  update {plan.stack.name}  →  {plan.root}\n")
    source = (
        f"{RECORD_NAME}, generated by newstack {plan.generated_by}"
        if plan.record_present
        else "--stack, no record"
    )
    print(f"  {'stack':<13} {plan.stack.name} ({source})")

    if plan.changes:
        verb = "would write" if dry_run else "wrote"
        written = [action for action in plan.changes if action.kind != ORPHAN]
        removed = [action for action in plan.changes if action.kind == ORPHAN]
        if written:
            print(f"  {verb:<13} {_count(len(written))}")
            for action in written:
                mark = "+" if action.kind == ADD else "~"
                print(f"      {mark} {action.rel}")
            forced = [a for a in written if a.kind == CONFLICT]
            if forced:
                print(f"  {'overwrote':<13} {_count(len(forced))} you had edited (--force)")
        if removed:
            label = "would delete" if dry_run else "deleted"
            print(f"  {label:<13} {_count(len(removed))}")
            for action in removed:
                print(f"      - {action.rel}")
    elif not plan.conflicts and not plan.of_kind(ORPHAN, ORPHAN_EDITED):
        print(f"  {'up to date':<13} every file already matches the template")

    if plan.conflicts and not plan.force:
        differs = "differs" if len(plan.conflicts) == 1 else "differ"
        print(
            f"  {'conflict':<13} {_count(len(plan.conflicts))} {differs}"
            " — left untouched"
        )
        for action in plan.conflicts:
            print(f"      ! {action.rel}")
            print(f"        {action.note}")

    untouched = plan.of_kind(UNCHANGED)
    if untouched:
        print(f"  {'unchanged':<13} {_count(len(untouched))}")

    kept = plan.of_kind(ORPHAN)
    if kept and not plan.prune:
        print(f"  {'dropped':<13} {_count(len(kept))} no longer in the template")
        for action in kept:
            print(f"      = {action.rel}")
        print(f"  {'':<13} rerun with --prune to delete the ones you never edited")

    edited = plan.of_kind(ORPHAN_EDITED)
    if edited:
        print(f"  {'orphaned':<13} {_count(len(edited))} edited locally, gone upstream")
        for action in edited:
            print(f"      = {action.rel}")

    if plan.conflicts and not plan.force:
        print("\n  keep your edits, or take the template's:")
        print(f"    git -C {plan.root} diff --stat")
        print(f"    newstack update {plan.root} --force")
    if not dry_run:
        print(f"  {'record':<13} {RECORD_NAME} updated (newstack {__version__})")
    print()


def cmd_outdated(args: argparse.Namespace) -> int:
    root = Path(args.path).expanduser().resolve()
    if not root.is_dir():
        raise TemplateError(f"not a directory: {root}")

    record = read_record(root)
    if record is None:
        raise TemplateError(
            f"no {RECORD_NAME} in {root} — `outdated` compares against the record "
            "`newstack new` writes; nothing to compare this project to"
        )
    stack = get_stack(record.stack)

    plan = plan_update(stack, root, record=record, context=dict(record.context))
    behind = plan.of_kind(UPDATE)
    missing = plan.of_kind(ADD)
    modified = plan.of_kind(CONFLICT)
    dropped = plan.of_kind(ORPHAN, ORPHAN_EDITED)
    stale = bool(behind or missing)

    if args.json:
        print(
            json.dumps(
                {
                    "stack": stack.name,
                    "root": str(root),
                    "record_version": record.version,
                    "newstack_version": __version__,
                    "updates_available": stale,
                    "behind": [a.rel for a in behind],
                    "missing": [a.rel for a in missing],
                    "modified": [a.rel for a in modified],
                    "dropped": [a.rel for a in dropped],
                },
                indent=2,
            )
        )
        return 1 if stale else 0

    print(f"\nnewstack {__version__}  ·  outdated {stack.name}  →  {root}\n")
    source = f"{RECORD_NAME}, generated by newstack {record.version or 'unknown'}"
    print(f"  {'stack':<13} {stack.name} ({source})")
    if record.version and record.version != __version__:
        print(f"  {'newstack':<13} {record.version} → {__version__}")

    if behind:
        print(f"  {'behind':<13} {_count(len(behind))} newer in the template")
        for action in behind:
            print(f"      ~ {action.rel}")
    if missing:
        print(f"  {'missing':<13} {_count(len(missing))} the template adds")
        for action in missing:
            print(f"      + {action.rel}")
    if modified:
        print(f"  {'modified':<13} {_count(len(modified))} you edited — update will conflict")
        for action in modified:
            print(f"      ! {action.rel}")
    if dropped:
        print(f"  {'dropped':<13} {_count(len(dropped))} the template no longer ships")
        for action in dropped:
            print(f"      = {action.rel}")
    if not (behind or missing or modified or dropped):
        print(f"  {'up to date':<13} this project matches the current template")

    if stale:
        print(f"\n  newstack update {root}")
    print()
    return 1 if stale else 0


def cmd_list(args: argparse.Namespace) -> int:
    catalog = load_catalog()
    stacks = catalog.stacks
    for name, reason in catalog.errors.items():
        print(f"  ! {name}: not loaded — {reason}", file=sys.stderr)
    if args.json:
        print(
            json.dumps(
                [
                    {
                        "name": s.name,
                        "title": s.title,
                        "language": s.language,
                        "blurb": s.blurb,
                        "requires": list(s.requires),
                        "available": not missing_tools(s),
                        "missing_tools": missing_tools(s),
                    }
                    for s in stacks.values()
                ],
                indent=2,
            )
        )
        return 0

    width = max((len(s.name) for s in stacks.values()), default=8)
    note = f" ({len(catalog.errors)} unusable)" if catalog.errors else ""
    print(f"\n{len(stacks)} stacks available{note}\n")
    for stack in stacks.values():
        absent = missing_tools(stack)
        flag = "" if not absent else f"  (needs {', '.join(absent)})"
        print(f"  {stack.name:<{width}}  {stack.language:<8}  {stack.blurb}{flag}")
    print("\n  scaffold one:  newstack new <stack> <path>\n")
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    names = list(args.stacks or [])
    broken: dict[str, str] = {}
    if args.all:
        catalog = load_catalog()
        available = catalog.stacks
        names = list(available)
        broken = catalog.errors
    else:
        available = {name: get_stack(name) for name in names}
    if not names:
        raise RegistryError("name at least one stack, or pass --all")

    results = []
    for name in names:
        stack = available[name]
        context = build_context_for_check(stack, args.name)
        absent = missing_tools(stack)
        if absent and not args.force:
            print(f"  {stack.name:<16} SKIP  missing toolchain: {', '.join(absent)}")
            continue
        print(f"  {stack.name:<16} running…", end="", flush=True)
        result = check_stack(stack, context, keep=args.keep, verbose=args.verbose)
        results.append(result)
        status = "PASS" if result.ok else "FAIL"
        print(f"\r  {stack.name:<16} {status}  {result.seconds:5.1f}s  "
              f"{len(result.outcomes)} step(s)          ")
        for outcome in result.outcomes:
            if outcome.skipped:
                print(f"      - {outcome.name}: skipped ({outcome.skipped})")
            elif not outcome.ok:
                print(f"      ✗ {outcome.name} failed in {outcome.seconds:.1f}s")
                if outcome.output:
                    for line in outcome.output.splitlines()[-25:]:
                        print(f"        {line}")
            elif args.verbose:
                print(f"      ✓ {outcome.name} ({outcome.seconds:.1f}s)")
        if args.keep:
            print(f"      generated project kept at {result.directory}")

    if broken:
        for name, reason in broken.items():
            print(f"  {name:<16} FAIL  stack directory is unusable: {reason}")

    if args.json:
        print(json.dumps([r.as_dict() for r in results], indent=2))
    green = bool(results) and all(r.ok for r in results) and not broken
    return 0 if green else 1


def build_context_for_check(stack: Stack, name: str | None) -> dict:
    args = argparse.Namespace(
        name=name or "check-app", description=None, author="newstack CI", email=None
    )
    return build_context(stack, Path(args.name), args)


def cmd_doctor(args: argparse.Namespace) -> int:
    print(f"\nnewstack {__version__}  ·  python {sys.version.split()[0]}\n")
    for tool, label in TOOLCHAIN_CHECKS.items():
        path = shutil.which(tool)
        mark = "✓" if path else "·"
        print(f"  {mark} {tool:<8} {label:<28} {path or 'not found'}")
    catalog = load_catalog()
    stacks = catalog.stacks
    for name, reason in catalog.errors.items():
        print(f"    ! {name}: unusable — {reason}")
    ready = [s.name for s in stacks.values() if not missing_tools(s)]
    blocked = {s.name: missing_tools(s) for s in stacks.values() if missing_tools(s)}
    print(f"\n  {len(ready)}/{len(stacks)} stacks can be verified on this machine")
    for name, absent in blocked.items():
        print(f"    ! {name}: needs {', '.join(absent)}")
    print()
    return 0


def cmd_version(args: argparse.Namespace) -> int:
    print(__version__ if not args.json else json.dumps({"version": __version__}))
    return 0


# --------------------------------------------------------------------------- parser


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="newstack",
        description="Scaffold a new project on any popular stack — every starter is CI-green.",
    )
    parser.add_argument("--version", action="version", version=f"newstack {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    new = sub.add_parser("new", help="create a project from a stack")
    new.add_argument("stack", help="stack name (see `newstack list`)")
    new.add_argument("path", help="directory to create")
    new.add_argument("--name", help="project name (defaults to the directory name)")
    new.add_argument("-d", "--description", help="one-line project description")
    new.add_argument("--author", help="author name (defaults to git config user.name)")
    new.add_argument("--email", help="author email (defaults to git config user.email)")
    new.add_argument(
        "--force", action="store_true", help="overwrite files in a non-empty directory"
    )
    new.add_argument("--dry-run", action="store_true", help="show what would be created")
    new.add_argument("--no-git", action="store_true", help="skip git init and first commit")
    new.add_argument(
        "--github",
        nargs="?",
        const=True,
        default=False,
        metavar="OWNER/REPO",
        help="create a GitHub repo from the project and push (needs gh)",
    )
    new.add_argument("--private", action="store_true", help="make the GitHub repo private")
    new.add_argument("--json", action="store_true", help="machine readable output")
    new.set_defaults(handler=cmd_new)

    adopt = sub.add_parser(
        "adopt", help="retrofit a stack's CI/lint files onto an existing project"
    )
    adopt.add_argument("path", help="directory of the existing project")
    adopt.add_argument("--stack", help="force a stack instead of auto-detecting")
    adopt.add_argument(
        "--with-tests", action="store_true", help="also copy the stack's starter tests"
    )
    adopt.add_argument("--dry-run", action="store_true", help="report without writing anything")
    adopt.add_argument("--author", help="author name for rendered files")
    adopt.add_argument("--email", help="author email for rendered files")
    adopt.add_argument("--json", action="store_true", help="machine readable output")
    adopt.set_defaults(handler=cmd_adopt, name=None, description=None)

    update = sub.add_parser(
        "update", help="re-apply template changes to a project newstack generated"
    )
    update.add_argument("path", help="directory of the generated project")
    update.add_argument("--stack", help="track this stack instead of the recorded one")
    update.add_argument("-d", "--description", help="override the recorded description")
    update.add_argument("--author", help="override the recorded author")
    update.add_argument("--email", help="override the recorded email")
    update.add_argument(
        "--force", action="store_true", help="overwrite files you edited locally"
    )
    update.add_argument(
        "--prune", action="store_true", help="delete unedited files the template dropped"
    )
    update.add_argument("--dry-run", action="store_true", help="report without writing anything")
    update.add_argument("--json", action="store_true", help="machine readable output")
    update.set_defaults(handler=cmd_update, name=None)

    stale = sub.add_parser(
        "outdated", help="report template changes a project has not taken yet"
    )
    stale.add_argument("path", nargs="?", default=".", help="project directory")
    stale.add_argument("--json", action="store_true", help="machine readable output")
    stale.set_defaults(handler=cmd_outdated)

    lst = sub.add_parser("list", help="list available stacks")
    lst.add_argument("--json", action="store_true")
    lst.set_defaults(handler=cmd_list)

    check = sub.add_parser("check", help="generate a stack in a temp dir and run its checks")
    check.add_argument("stacks", nargs="*", help="stack names")
    check.add_argument("--all", action="store_true", help="check every stack")
    check.add_argument("--keep", action="store_true", help="keep the generated project")
    check.add_argument("--verbose", action="store_true", help="show passing step output")
    check.add_argument("--force", action="store_true", help="run even if tools look missing")
    check.add_argument("--name", help="project name for the generated sample")
    check.add_argument("--json", action="store_true")
    check.set_defaults(handler=cmd_check)

    doctor = sub.add_parser("doctor", help="show which toolchains are installed")
    doctor.set_defaults(handler=cmd_doctor)

    version = sub.add_parser("version", help="print the version")
    version.add_argument("--json", action="store_true")
    version.set_defaults(handler=cmd_version)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
    except (RegistryError, TemplateError) as exc:
        print(f"newstack: error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
