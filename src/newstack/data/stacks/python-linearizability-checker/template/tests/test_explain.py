from {{ package_name }} import explain as subject
from {{ package_name }} import history as history_module
from {{ package_name }}.check import check


def op(client, kind, value, start, end):
    return history_module.Operation(client=client, kind=kind, value=value, start=start, end=end)


def test_a_witness_lists_the_order_one_per_line():
    facts = history_module.History((op(0, "write", 1, 0, 1), op(0, "read", 1, 2, 3)))
    lines = subject.witness_lines(facts, check(facts))
    assert lines[0].startswith("  1  client 0 write 1")
    assert len(lines) == 2


def test_a_verdict_reports_the_search_it_did():
    facts = history_module.History((op(0, "write", 1, 0, 1),))
    text = "\n".join(subject.verdict_lines(facts, check(facts)))
    assert "verdict    linearizable" in text
    assert "search     1 node(s)" in text
    assert "witness    one order that holds:" in text


def test_a_refusal_reports_a_core():
    facts = history_module.History((op(0, "write", 5, 0, 2), op(1, "read", 0, 3, 4)))
    text = "\n".join(subject.verdict_lines(facts, check(facts)))
    assert "verdict    not linearizable" in text
    assert "core       2 of 2 operation(s)" in text
    assert "removing any one" in text


def test_a_core_line_names_each_operation():
    facts = history_module.History((op(0, "write", 5, 0, 2), op(1, "read", 0, 3, 4)))
    lines = subject.verdict_lines(facts, check(facts))
    cores = [line for line in lines if line.startswith("  client")]
    assert len(cores) == 2


def test_an_account_groups_operations_by_client():
    facts = history_module.History(
        (op(0, "write", 1, 0, 1), op(1, "read", 1, 2, 3), op(0, "read", 1, 4, 5))
    )
    lines = subject.account_lines(facts)
    assert lines[0] == "client 0  2 operation(s)"
    assert lines[1].strip().startswith("client 0 write 1")
    assert lines[3] == "client 1  1 operation(s)"
