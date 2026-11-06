"""Delivery: what waits, what does not, and how a break is counted."""

import pytest

from {{ package_name }} import causal as subject
from {{ package_name }} import vector


def pair():
    """a writes, b reads it and answers, so the answer depends on the write."""
    ids = subject.Ids()
    a = subject.Replica("a", ids=ids)
    b = subject.Replica("b", ids=ids)
    first = a.send("b", "the price changed")
    b.receive(first)
    answer = b.send("c", "agreed")
    return a, b, first, answer


def test_a_send_advances_the_sender_and_records_the_state():
    a, _, first, _ = pair()
    assert a.state.text() == "a:1"
    assert first.deps.text() == "a:1"
    assert first.sender == "a"
    assert first.target == "b"


def test_a_reply_depends_on_what_was_received():
    _, _, first, answer = pair()
    assert answer.deps.get("a") == first.deps.get("a")
    assert answer.deps.get("b") == 1


def test_a_message_with_a_missing_dependency_is_held():
    _, _, _write, answer = pair()
    late = subject.Replica("c")
    assert late.receive(answer) == "held"
    assert len(late.held) == 1
    assert not late.delivered


def test_the_arrival_of_the_dependency_releases_it():
    _, _, first, answer = pair()
    late = subject.Replica("c")
    late.receive(answer)
    assert late.receive(first) == "delivered"
    released = late.drain()
    assert [message.id for message in released] == [answer.id]
    assert [message.id for message in late.delivered] == [first.id, answer.id]


def test_a_gated_delivery_never_breaks_causality():
    _, _, first, answer = pair()
    late = subject.Replica("c")
    late.receive(answer)
    late.receive(first)
    late.drain()
    assert subject.causality_violations(late.delivered) == []


def test_an_ungated_delivery_breaks_causality():
    _, _, first, answer = pair()
    naive = subject.Replica("d", gated=False)
    naive.receive(answer)
    naive.receive(first)
    broken = subject.causality_violations(naive.delivered)
    assert len(broken) == 1
    message, node, needed, had = broken[0]
    assert message.id == answer.id
    assert (node, needed, had) == ("a", 1, 0)


def test_a_break_prints_as_a_line():
    _, _, _write, answer = pair()
    naive = subject.Replica("d", gated=False)
    naive.receive(answer)
    lines = subject.describe_violations(subject.causality_violations(naive.delivered))
    assert len(lines) == 1
    assert lines[0].startswith("m")
    assert "needed a at 1" in lines[0]


def test_a_clean_order_has_no_lines():
    assert subject.describe_violations([]) == []


def test_an_empty_delivery_has_no_breaks():
    assert subject.causality_violations([]) == []


def test_a_local_event_has_no_target_and_advances_the_counter():
    replica = subject.Replica("solo")
    event = replica.local("think")
    assert event.node == "solo"
    assert event.text().startswith("L1 solo state[solo:1]")
    assert replica.state.text() == "solo:1"


def test_the_replica_state_is_the_merge_of_what_it_has_delivered():
    _, _, first, answer = pair()
    receiver = subject.Replica("c")
    receiver.receive(first)
    receiver.receive(answer)
    assert receiver.state.get("a") == 1
    assert receiver.state.get("b") == 1
    assert receiver.state.compare(vector.VersionVector.parse("a:1,b:1")) is vector.Relation.EQUAL


def test_ids_are_never_reused_across_replicas():
    ids = subject.Ids()
    first = subject.Replica("a", ids=ids).send("b", "one")
    second = subject.Replica("b", ids=ids).send("a", "two")
    assert first.id != second.id


def test_a_message_to_itself_is_refused():
    with pytest.raises(subject.CausalError, match="itself"):
        subject.Message(1, "a", "a", vector.VersionVector.empty(), "note")


def test_a_message_needs_a_positive_id():
    with pytest.raises(subject.CausalError, match="at least 1"):
        subject.Message(0, "a", "b", vector.VersionVector.empty(), "note")


def test_a_message_needs_a_sender_and_a_target():
    with pytest.raises(subject.CausalError, match="needs a"):
        subject.Message(1, "", "b", vector.VersionVector.empty(), "note")


def test_a_replica_needs_a_node():
    with pytest.raises(subject.CausalError, match="node name"):
        subject.Replica("")


def test_a_message_prints_its_dependencies():
    _, _, first, _ = pair()
    assert "deps[a:1]" in first.text()
