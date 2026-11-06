"""Six stories: what a total order loses, and what a vector costs to keep."""

from __future__ import annotations

from dataclasses import dataclass, field

from . import causal, lamport, prune
from .vector import Relation, VersionVector, explain, merge_all


@dataclass
class Story:
    title: str
    lines: list[str] = field(default_factory=list)
    held: bool = True

    def line(self, text: str) -> None:
        self.lines.append(f"  {text}")

    def require(self, condition: bool) -> None:
        self.held = self.held and condition


def story_total_order() -> Story:
    """Two replicas that never spoke, ordered by a clock that only counts."""
    draft = lamport.Event("draft the note", lamport.busy("a", 2).tick())
    rushed = lamport.Event("comment on it", lamport.LamportClock("b").tick())
    settled = lamport.Event("comment on it", lamport.busy("b", 5).tick())

    story = Story("1. a Lamport order is total, and the order is an artifact")
    first = lamport.order([draft, rushed])
    second = lamport.order([draft, settled])
    story.line("the two replicas never exchanged a message, so both events are concurrent")
    story.line(f"idle replica  {first[0].stamp.text()} then {first[1].stamp.text()}")
    story.line(f"busy replica  {second[0].stamp.text()} then {second[1].stamp.text()}")
    story.line("five unrelated local events were enough to put the comment on the other side")
    story.require(lamport.precedes(rushed, draft))
    story.require(lamport.precedes(draft, settled))
    story.require(not lamport.precedes(draft, rushed))
    return story


def story_vector_refuses() -> Story:
    """The same two events, as vectors, with a verdict that does not depend on arrival."""
    left = VersionVector({"a": 1})
    right = VersionVector({"b": 1})
    story = Story("2. a version vector refuses to order them")
    story.line(f"left         {left.text()}")
    story.line(f"right        {right.text()}")
    story.line(f"relation     {left.compare(right).value}")
    story.line(f"why          {explain(left, right)}")
    story.line(f"lamport says {lamport.Stamp(1, 'a').text()} before {lamport.Stamp(1, 'b').text()}")
    story.require(left.compare(right) is Relation.CONCURRENT)
    story.require(not left.before(right) and not right.before(left))
    after = VersionVector({"a": 1, "b": 1})
    story.line(f"after merge  {after.text()}, which is after both")
    story.require(left.before(after) and right.before(after))
    return story


def story_join() -> Story:
    """Merge has to be a join, or the order of merges would matter."""
    vectors = [
        VersionVector({"a": 2, "b": 1}),
        VersionVector({"b": 3, "c": 1}),
        VersionVector({"a": 1, "c": 4}),
    ]
    joined = merge_all(vectors)
    story = Story("3. the merge is a join, so order and repetition do not matter")
    story.line("vectors      " + " , ".join(vector.text() for vector in vectors))
    story.line(f"merged       {joined.text()}")
    idempotent = joined.merge(joined) == joined
    commutative = vectors[0].merge(vectors[1]) == vectors[1].merge(vectors[0])
    associative = vectors[0].merge(vectors[1]).merge(vectors[2]) == vectors[0].merge(
        vectors[1].merge(vectors[2])
    )
    story.line(f"idempotent   {idempotent}")
    story.line(f"commutative  {commutative}")
    story.line(f"associative  {associative}")
    reversed_fold = merge_all(list(reversed(vectors)))
    story.line(
        f"reversed     {reversed_fold.text()}, which is the same vector: {reversed_fold == joined}"
    )
    story.require(idempotent and commutative and associative)
    story.require(reversed_fold == joined)
    story.require(joined.get("c") == 4 and joined.get("b") == 3)
    return story


def _handoff() -> tuple[
    causal.Replica, causal.Replica, causal.Replica, causal.Message, causal.Message
]:
    """a writes, b reads it and answers, and c receives the answer before the original."""
    ids = causal.Ids()
    a = causal.Replica("a", ids=ids)
    b = causal.Replica("b", ids=ids)
    c = causal.Replica("c", ids=ids)
    first = a.send("b", "the price changed")
    b.receive(first)
    answer = b.send("c", "agreed, at the new price")
    return a, b, c, first, answer


def story_causal_delivery() -> Story:
    """Arrival order is not causal order, and one comparison tells them apart."""
    story = Story("4. causal delivery holds a message it cannot yet deliver")

    _, _, naive, first, answer = _handoff()
    naive.gated = False
    naive.receive(answer)
    naive.receive(first)
    broken = causal.causality_violations(naive.delivered)
    story.line(f"no gate      delivered {[f'm{m.id}' for m in naive.delivered]}")
    story.line(
        f"breaks       {len(broken)}: " + (causal.describe_violations(broken) or ["none"])[0]
    )

    _, _, gated, first, answer = _handoff()
    verdict = gated.receive(answer)
    held = len(gated.held)
    released = gated.receive(first)
    drained = gated.drain()
    story.line(f"gated        m{answer.id} was {verdict}, {held} held")
    story.line(
        f"then         m{first.id} was {released}, releasing {[f'm{m.id}' for m in drained]}"
    )
    story.line(f"delivered    {[f'm{m.id}' for m in gated.delivered]}")
    story.line(f"breaks       {len(causal.causality_violations(gated.delivered))}")
    story.require(len(broken) == 1)
    story.require(verdict == "held")
    story.require([message.id for message in gated.delivered] == [first.id, answer.id])
    story.require(not causal.causality_violations(gated.delivered))
    return story


def story_compaction() -> Story:
    """Where compaction is exact, and where it quietly changes the answer."""
    above = [
        VersionVector({"a": 3, "b": 2, "c": 1}),
        VersionVector({"a": 3, "b": 4, "c": 1}),
        VersionVector({"a": 5, "b": 4, "c": 1}),
        VersionVector({"a": 5, "b": 4, "c": 2}),
    ]
    below = [
        VersionVector({"a": 0, "b": 1, "c": 1}),
        VersionVector({"a": 1, "b": 1, "c": 1}),
        VersionVector({"a": 2, "b": 0, "c": 1}),
    ]
    floor = VersionVector({"a": 3, "b": 2, "c": 1})
    story = Story("5. compaction is exact above the floor and lossy below it")

    measured = prune.measure(above + below, floor)
    story.line(f"floor        {floor.text()}")
    for line in measured.lines():
        story.line(line)
    for example in measured.examples_below:
        story.line(f"changed      {example}")
    story.require(measured.changed_above == 0)
    story.require(measured.changed_below > 0)
    story.require(measured.above == 6 and measured.below == 15)
    return story


def story_width() -> Story:
    """The width of a vector is the number of writers it still has to remember."""
    writers = [f"w{number}" for number in range(8)]
    full = VersionVector({writer: number + 1 for number, writer in enumerate(writers)})
    floor = VersionVector({writer: number + 1 for number, writer in enumerate(writers[:5])})
    squeezed = prune.compact(full, floor)
    story = Story("6. the width is the number of writers still being tracked")
    story.line(f"full         {full.text()} ({len(full)} entries)")
    story.line(f"floor        {floor.text()} ({len(floor)} entries)")
    story.line(f"compacted    {squeezed.text()} ({len(squeezed)} entries)")
    story.line(
        f"the five writers at the floor are past on every replica, so their counters "
        f"distinguish nothing and {len(full) - len(squeezed)} entries go"
    )
    story.require(len(squeezed) == 3)
    story.require(squeezed.text() == "w5:6,w6:7,w7:8")
    return story


STORIES = (
    story_total_order,
    story_vector_refuses,
    story_join,
    story_causal_delivery,
    story_compaction,
    story_width,
)


def render_stories() -> tuple[list[str], bool]:
    rows: list[str] = []
    held = True
    for builder in STORIES:
        story = builder()
        rows.append(story.title)
        rows.extend(story.lines)
        rows.append(f"  -> {'holds' if story.held else 'BROKEN'}")
        rows.append("")
        held = held and story.held
    return rows, held


def main() -> int:
    rows, held = render_stories()
    print("\n".join(rows))
    return 0 if held else 1


if __name__ == "__main__":
    raise SystemExit(main())
