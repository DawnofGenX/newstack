"""Offline checks: no sockets, no files outside a temp dir, one line of output."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from {{ package_name }} import runner
from {{ package_name }}.client import ChatClient, RequestFailed
from {{ package_name }}.records import (
    RecordError,
    Request,
    Result,
    ResultWriter,
    load_results,
    parse_requests,
    parse_results,
)


class FakeClient(ChatClient):
    """Never touches the network; answers or fails on a fixed script."""

    def __init__(self, *, fail_on: str = "") -> None:
        super().__init__("http://stub.invalid/v1", model="fake-model", max_attempts=1)
        self.fail_on = fail_on
        self.prompts: list[str] = []

    def complete(self, prompt: str) -> tuple[str, int, int, int]:
        self.prompts.append(prompt)
        if prompt == self.fail_on:
            raise RequestFailed("http 400")
        return f"echo: {prompt}", len(prompt.split()), 1, 1


def run() -> int:
    """Return the exit code: 0 when every check passed."""
    checks = 0

    def ok(condition: bool, label: str) -> None:
        nonlocal checks
        checks += 1
        if not condition:
            raise SystemExit(f"selftest: FAIL {label}")

    requests = parse_requests(['{"id": "a", "prompt": "hi"}', "", '{"id": "b", "prompt": "yo"}'])
    ok(len(requests) == 2, "blank lines are skipped")
    ok(requests[0].id == "a", "ids are read in order")

    for bad, label in [
        ('[{"id": "a", "prompt": "hi"}]', "a JSON array is not a record"),
        ('{"id": "a"}', "a request needs a prompt"),
        ('{"prompt": "hi"}', "a request needs an id"),
        ('{"id": "", "prompt": "hi"}', "an empty id is rejected"),
        ('{"id": "a", "prompt": "x"}\n{"id": "a", "prompt": "y"}', "duplicate ids are rejected"),
        ("", "an empty batch is rejected"),
        ("not json", "a non-JSON line is rejected"),
    ]:
        try:
            parse_requests(bad.splitlines())
        except RecordError:
            ok(True, label)
        else:
            ok(False, label)

    done = parse_results(['{"id": "a", "output": "x"}', '{"id": "b", "outp'])
    ok(list(done) == ["a"], "a torn final result line is discarded")
    ok(done["a"].output == "x", "results keep their output")

    result = Result(id="a", output="héllo", tokens_in=2, tokens_out=3, attempts=1)
    ok(Result.from_line(result.line()) == result, "a result survives a round trip")

    client = FakeClient(fail_on="boom")
    answered = runner.one(client, Request(id="a", prompt="hi there"))
    ok(answered.ok and answered.tokens_in == 2, "one() records token counts")
    ok(answered.model == "fake-model", "one() records the model")
    refused = runner.one(client, Request(id="b", prompt="boom"))
    ok(not refused.ok and refused.error == "http 400", "one() records failures instead of raising")

    with tempfile.TemporaryDirectory() as directory:
        out = Path(directory) / "results.jsonl"
        with ResultWriter(out) as writer:
            batch = [Request(id=f"r{index}", prompt="hi") for index in range(4)]
            summary = runner.run(batch, FakeClient(), writer, concurrency=2)
        ok(summary.ok == 4 and summary.failed == 0, "every request is answered")
        ok(summary.resumed == 0, "nothing was resumed")
        ok(len(out.read_text().splitlines()) == 4, "one line per request is written")
        again = load_results(out)
        ok(sorted(again) == ["r0", "r1", "r2", "r3"], "a rerun can tell what is done")
        with ResultWriter(out) as writer:
            second = runner.run([Request(id="r1", prompt="hi")], FakeClient(), writer, resumed=1)
        ok(second.worked == 1, "only the pending request is sent on a rerun")

    payload = json.loads(ChatClient("http://stub.invalid/v1", model="m").payload("hi"))
    ok(payload["model"] == "m", "the payload carries the model")
    ok(payload["messages"][0]["content"] == "hi", "the payload carries the prompt")

    print(f"selftest: {checks} checks passed")
    return 0
