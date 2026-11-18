"""Typer command-line entry point."""

from __future__ import annotations

import sys
from pathlib import Path

import typer

from .storage import load, save

app = typer.Typer(help="A small task tracker.")


def _path(file: Path | None) -> Path:
    return file if file is not None else Path("tasks.json")


@app.command()
def add(
    text: str = typer.Argument(..., help="Task description."),
    file: Path | None = typer.Option(None, "--file", help="Task store path."),
) -> None:
    """Add a new task."""
    path = _path(file)
    tasks = load(path)
    next_id = max((int(t.get("id", 0)) for t in tasks), default=0) + 1
    tasks.append({"id": next_id, "text": text, "done": False})
    save(path, tasks)
    typer.echo(f"added {next_id}: {text}")


@app.command("list")
def list_tasks(
    file: Path | None = typer.Option(None, "--file", help="Task store path."),
) -> None:
    """List all tasks."""
    tasks = load(_path(file))
    if not tasks:
        typer.echo("no tasks")
        return
    for task in tasks:
        mark = "x" if task.get("done") else " "
        typer.echo(f"[{mark}] {task['id']}: {task['text']}")


@app.command()
def done(
    task_id: int = typer.Argument(..., help="Task id."),
    file: Path | None = typer.Option(None, "--file", help="Task store path."),
) -> None:
    """Mark a task done."""
    path = _path(file)
    tasks = load(path)
    for task in tasks:
        if int(task.get("id", -1)) == task_id:
            task["done"] = True
            save(path, tasks)
            typer.echo(f"done {task_id}")
            return
    typer.echo(f"not found: {task_id}", err=True)
    raise typer.Exit(code=1)


@app.command("rm")
def remove(
    task_id: int = typer.Argument(..., help="Task id."),
    file: Path | None = typer.Option(None, "--file", help="Task store path."),
) -> None:
    """Remove a task."""
    path = _path(file)
    tasks = load(path)
    kept = [t for t in tasks if int(t.get("id", -1)) != task_id]
    if len(kept) == len(tasks):
        typer.echo(f"not found: {task_id}", err=True)
        raise typer.Exit(code=1)
    save(path, kept)
    typer.echo(f"removed {task_id}")


def main() -> int:
    if "--selftest" in sys.argv:
        from typer.testing import CliRunner

        runner = CliRunner()
        store = Path("tasks_selftest.json")
        try:
            result = runner.invoke(app, ["add", "buy milk", "--file", str(store)])
            assert result.exit_code == 0, result.output
            assert "added 1" in result.output
            result = runner.invoke(app, ["list", "--file", str(store)])
            assert result.exit_code == 0, result.output
            assert "buy milk" in result.output
            result = runner.invoke(app, ["done", "1", "--file", str(store)])
            assert result.exit_code == 0, result.output
            result = runner.invoke(app, ["rm", "1", "--file", str(store)])
            assert result.exit_code == 0, result.output
        finally:
            store.unlink(missing_ok=True)
        print("selftest: ok")
        return 0
    app()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
