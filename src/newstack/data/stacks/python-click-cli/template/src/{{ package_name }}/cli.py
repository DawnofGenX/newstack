"""Click command-line entry point."""

from __future__ import annotations

import click


@click.group()
def cli() -> None:
    """A small Click toolkit."""


@cli.command()
@click.option("--name", default="world", help="Name to greet.")
def greet(name: str) -> None:
    click.echo(f"hello {name}")


@cli.command()
@click.argument("text")
def count(text: str) -> None:
    words = text.split()
    click.echo(f"words={len(words)} chars={len(text)}")


def main() -> int:
    return cli() or 0


if __name__ == "__main__":
    raise SystemExit(main())