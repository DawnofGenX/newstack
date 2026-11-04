"""``newstack update``: re-apply a stack's current template to a generated project.

``newstack new`` records what it wrote in ``.newstack.json`` — the render context and a
sha256 per generated file. ``update`` re-renders the *current* template with that
recorded context, then merges three inputs per file:

    recorded   what newstack last wrote
    disk       what the project has now
    template   what the stack ships today

A file nobody touched is safe to refresh. A file the user edited is a conflict and is
left alone unless ``--force``. A file the template stopped shipping is reported, and is
only deleted with ``--prune`` and only while it still matches what newstack wrote — so
update can never eat work the user did.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from . import __version__
from .registry import Stack
from .render import TemplateError, render_tree

RECORD_NAME = ".newstack.json"

ADD = "add"
UPDATE = "update"
UNCHANGED = "unchanged"
CONFLICT = "conflict"
ORPHAN = "orphan"
ORPHAN_EDITED = "orphan-edited"

KIND_ORDER = (UPDATE, ADD, CONFLICT, UNCHANGED, ORPHAN, ORPHAN_EDITED)

KIND_LABELS = {
    UPDATE: "update",
    ADD: "add",
    UNCHANGED: "unchanged",
    CONFLICT: "conflict",
    ORPHAN: "removed upstream",
    ORPHAN_EDITED: "removed upstream, edited",
}


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str | None:
    try:
        return sha256_bytes(path.read_bytes())
    except OSError:
        return None


# --------------------------------------------------------------------------- record


@dataclass(frozen=True)
class Record:
    """What ``newstack new`` left behind in ``.newstack.json``."""

    stack: str
    context: dict
    files: dict[str, str]
    version: str = ""


def read_record(root: Path | str) -> Record | None:
    """Return the record in *root*, or ``None`` when the project has none."""
    path = Path(root) / RECORD_NAME
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TemplateError(f"{path}: unreadable record ({exc})") from exc
    if not isinstance(data, dict):
        raise TemplateError(f"{path}: top level must be an object")
    stack = data.get("stack")
    context = data.get("context")
    files = data.get("files", {})
    if not isinstance(stack, str) or not stack:
        raise TemplateError(f"{path}: missing 'stack'")
    if not isinstance(context, dict) or not isinstance(context.get("project_name"), str):
        raise TemplateError(
            f"{path}: missing render context — regenerate the project with newstack"
        )
    if not isinstance(files, dict) or not all(
        isinstance(key, str) and isinstance(value, str) for key, value in files.items()
    ):
        raise TemplateError(f"{path}: 'files' must map paths to sha256 digests")
    return Record(
        stack=stack,
        context=dict(context),
        files=dict(files),
        version=str(data.get("version") or ""),
    )


def write_record(
    root: Path | str, stack: str, context: dict, files: dict[str, str]
) -> Path:
    """Write the record atomically, so an interrupted run cannot leave half a file."""
    root = Path(root)
    payload = {
        "tool": "newstack",
        "version": __version__,
        "stack": stack,
        "context": context,
        "files": dict(sorted(files.items())),
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    target = root / RECORD_NAME
    tmp = target.with_name(target.name + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, target)
    return target


# --------------------------------------------------------------------------- plan


@dataclass
class Action:
    rel: str
    kind: str
    note: str = ""


@dataclass
class UpdatePlan:
    root: Path
    stack: Stack
    actions: list[Action] = field(default_factory=list)
    directories: list[str] = field(default_factory=list)
    rendered: dict[str, tuple[bytes, bool]] = field(default_factory=dict)
    record_present: bool = True
    generated_by: str = ""
    context: dict = field(default_factory=dict)
    force: bool = False
    prune: bool = False

    def of_kind(self, *kinds: str) -> list[Action]:
        return [action for action in self.actions if action.kind in kinds]

    @property
    def conflicts(self) -> list[Action]:
        return self.of_kind(CONFLICT)

    @property
    def changes(self) -> list[Action]:
        """Everything the run writes or deletes."""
        kinds = {UPDATE, ADD}
        if self.prune:
            kinds.add(ORPHAN)
        if self.force:
            kinds.add(CONFLICT)
        return [action for action in self.actions if action.kind in kinds]

    @property
    def ok(self) -> bool:
        return self.force or not self.conflicts

    def as_dict(self) -> dict:
        return {
            "stack": self.stack.name,
            "path": str(self.root),
            "record": self.record_present,
            "generated_by": self.generated_by or None,
            "force": self.force,
            "prune": self.prune,
            "counts": {
                kind: len(self.of_kind(kind)) for kind in KIND_ORDER if self.of_kind(kind)
            },
            "actions": [
                {"path": action.rel, "action": action.kind, "note": action.note}
                for action in self.actions
                if action.kind != UNCHANGED
            ],
        }


def plan_update(
    stack: Stack,
    root: Path | str,
    *,
    record: Record | None = None,
    context: dict | None = None,
    force: bool = False,
    prune: bool = False,
) -> UpdatePlan:
    """Decide, per file, what updating *root* to *stack*'s template should do."""
    root = Path(root)
    if not root.is_dir():
        raise TemplateError(f"not a directory: {root}")
    if context is None:
        if record is None:
            raise TemplateError(
                "no render context: this project has no .newstack.json — pass --stack "
                "and the original --name/--author/-d, or regenerate it with newstack"
            )
        context = dict(record.context)

    merged = dict(context)
    merged["newstack_version"] = __version__
    entries, directories = render_tree(stack.template_dir, merged)

    plan = UpdatePlan(
        root=root,
        stack=stack,
        directories=list(directories),
        record_present=record is not None,
        generated_by=(record.version if record else ""),
        context=merged,
        force=force,
        prune=prune,
    )
    recorded = dict(record.files) if record else {}

    for rel, payload, executable in entries:
        plan.rendered[rel] = (payload, executable)
        new_hash = sha256_bytes(payload)
        target = root / rel
        disk_hash = _sha256_file(target) if target.is_file() else None

        if disk_hash is None:
            plan.actions.append(Action(rel, ADD))
        elif disk_hash == new_hash:
            plan.actions.append(Action(rel, UNCHANGED))
        elif recorded.get(rel) == disk_hash:
            plan.actions.append(Action(rel, UPDATE, "no local edits"))
        elif recorded.get(rel) is None:
            plan.actions.append(
                Action(
                    rel,
                    CONFLICT,
                    "not written by newstack — left alone; --force takes the template's",
                )
            )
        else:
            note = "locally edited; --force takes the template's version"
            plan.actions.append(Action(rel, CONFLICT, note))

    shipped = {rel for rel, _, _ in entries}
    for rel, old_hash in sorted(recorded.items()):
        if rel in shipped:
            continue
        target = root / rel
        disk_hash = _sha256_file(target)
        if disk_hash is None:
            continue  # already gone
        if disk_hash == old_hash:
            plan.actions.append(Action(rel, ORPHAN, "unchanged since generated"))
        else:
            plan.actions.append(Action(rel, ORPHAN_EDITED, "edited locally — never pruned"))

    order = {kind: index for index, kind in enumerate(KIND_ORDER)}
    plan.actions.sort(key=lambda action: (order.get(action.kind, 99), action.rel))
    return plan


def apply_update(plan: UpdatePlan, *, write_record_file: bool = True) -> list[Action]:
    """Carry out *plan*; returns the actions actually applied."""
    applied: list[Action] = []
    plan.root.mkdir(parents=True, exist_ok=True)
    for rel_dir in plan.directories:
        (plan.root / rel_dir).mkdir(parents=True, exist_ok=True)

    for action in plan.actions:
        target = plan.root / action.rel
        if action.kind in (ADD, UPDATE) or (action.kind == CONFLICT and plan.force):
            payload, executable = plan.rendered[action.rel]
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(payload)
            if executable:
                target.chmod(0o755)
            applied.append(action)
        elif action.kind == ORPHAN and plan.prune:
            try:
                target.unlink()
            except OSError:
                continue
            applied.append(action)

    if write_record_file and plan.record_present:
        previous = read_record(plan.root)
        applied_rel = {action.rel for action in applied}
        files: dict[str, str] = {}
        for action in plan.actions:
            rel = action.rel
            pruned = action.kind == ORPHAN and rel in applied_rel
            if action.kind == ORPHAN_EDITED or pruned:
                continue  # not ours any more (or just deleted)
            if action.kind == UNCHANGED or rel in applied_rel:
                files[rel] = sha256_bytes(plan.rendered[rel][0])
            elif previous and rel in previous.files:
                # Conflicts keep what newstack last wrote — recording the disk hash
                # would make the next run treat the user's edit as ours and overwrite
                # it. Unpruned orphans stay on record so --prune can find them later.
                files[rel] = previous.files[rel]
        # A no-op run must leave the record byte-identical: rewriting it would
        # bump ``updated_at`` and make "nothing changed" show up as a diff.
        current = (
            previous is not None
            and not applied
            and previous.stack == plan.stack.name
            and previous.context == plan.context
            and dict(previous.files) == files
            and previous.version == __version__
        )
        if not current:
            write_record(plan.root, plan.stack.name, plan.context, files)
    return applied
