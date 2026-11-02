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
from .registry import RegistryError, Stack, get_stack, load_stacks
from .render import TemplateError, generate
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


def _package_name(name: str) -> str:
    slug = re.sub(r"[^0-9A-Za-z]+", "_", name).strip("_").lower()
    if not slug:
        slug = "app"
    if slug[0].isdigit():
        slug = f"app_{slug}"
    if slug in PY_RESERVED:
        slug = f"{slug}_app"
    return slug


def _npm_name(name: str) -> str:
    slug = re.sub(r"[^a-z0-9._-]+", "-", name.lower()).strip("-._")
    return slug or "app"


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


def build_context(stack: Stack, destination: Path, args: argparse.Namespace) -> dict:
    project_name = args.name or destination.name
    author = args.author or _git_config("user.name") or "Your Name"
    email = args.email or _git_config("user.email") or "noreply@example.com"
    today = datetime.now(timezone.utc).date()
    return {
        "project_name": project_name,
        "package_name": _package_name(project_name),
        "npm_name": _npm_name(project_name),
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

    if stack.next_steps:
        steps = [
            step.format(
                path=destination,
                package_name=context["package_name"],
                npm_name=context["npm_name"],
                project_name=context["project_name"],
            )
            for step in stack.next_steps
        ]
        print("\n  next:")
        for step in steps:
            print(f"    {step}")
    print()


def cmd_list(args: argparse.Namespace) -> int:
    stacks = load_stacks()
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
    print(f"\n{len(stacks)} stacks available\n")
    for stack in stacks.values():
        absent = missing_tools(stack)
        flag = "" if not absent else f"  (needs {', '.join(absent)})"
        print(f"  {stack.name:<{width}}  {stack.language:<8}  {stack.blurb}{flag}")
    print("\n  scaffold one:  newstack new <stack> <path>\n")
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    names = list(args.stacks or [])
    if args.all:
        names = list(load_stacks())
    if not names:
        raise RegistryError("name at least one stack, or pass --all")

    results = []
    for name in names:
        stack = get_stack(name)
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

    if args.json:
        print(json.dumps([r.as_dict() for r in results], indent=2))
    return 0 if results and all(r.ok for r in results) else 1


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
    stacks = load_stacks()
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
