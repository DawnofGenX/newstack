# {{ title }}

A pytest plugin whose product is the report, not the assertions.

pytest already knows how long every phase of every test took. It prints that
knowledge to a terminal as text, and the text is gone when the terminal closes.
This plugin keeps it: one JSON file, one entry per test, one entry per phase,
with the ticket each test claims to cover — and a console script that turns the
file into a summary and a duration gate.

## Quick start

```bash
uv venv --allow-existing .venv
uv pip install --python .venv/bin/python -e . pytest ruff

.venv/bin/python -m pytest --testmeta-report report.json
.venv/bin/{{ npm_name }} summary report.json --top 5
```

```
total 42 tests, 40 passed, 1 failed, 1 skipped, 0 error
slowest
    312.400 ms  call      tests/test_api.py::test_round_trip  [ABC-114]
     88.910 ms  teardown  tests/test_api.py::test_round_trip  [ABC-114]
     41.050 ms  call      tests/test_db.py::test_migration    [ABC-118]
```

## The report

```json
{
  "format": 1,
  "exit_status": 1,
  "tests": [
    {
      "nodeid": "tests/test_api.py::test_round_trip",
      "outcome": "passed",
      "duration_ms": 401.31,
      "tickets": ["ABC-114"],
      "phases": {
        "setup": { "outcome": "passed", "duration_ms": 0.4 },
        "call": { "outcome": "passed", "duration_ms": 312.4 },
        "teardown": { "outcome": "passed", "duration_ms": 88.51 }
      }
    }
  ]
}
```

`format` is the contract. The loader refuses anything else with a message that
names the version it found, so an old CLI reading a new report fails loudly
instead of quietly ignoring the fields it does not know.

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | the summary was printed, or no test broke the duration limit |
| 1 | `--fail-over-ms` was given and at least one test went over it |
| 2 | the report could not be read, or the command line was wrong |
| 4 | pytest's own code for `--testmeta-strict` refusing an unmarked suite |

`4` is not this project's invention: `pytest.UsageError` is a usage problem, and
pytest answers usage problems with `ExitCode.USAGE_ERROR`.

## The traps

1. **The entry point is the plugin.** A `conftest.py` only affects the project
   it sits in; `[project.entry-points.pytest11]` in `pyproject.toml` is what
   makes `pip install -e .` turn a module into a plugin pytest loads for every
   run in that environment.
2. **A marker must be registered.** With `--strict-markers`, `@pytest.mark.ticket`
   is a hard error unless `pytest_configure` called `addinivalue_line("markers", ...)`.
   The decorator does not register anything.
3. **`wrapper=True`, not `hookwrapper=True`.** The wrapper form receives the
   result of `yield` and must return it; forgetting the `return` silently turns
   the test report into `None` and every test into an internal error.
4. **`pytest_runtest_makereport` runs once per phase.** A failure in `setup` or
   `teardown` is an **error**, not a failed assertion, and a report that calls
   everything "failed" hides the difference between "the test disagreed" and
   "the fixture broke".
5. **A skipped test never reaches the call phase.** Keying the report on the
   call phase alone drops every skipped test without a word.
6. **`pytester` runs in-process by default.** The plugin is already imported by
   the outer session, so `runpytest("-p", "{{ npm_name }}")` raises "Plugin
   already registered". Use `runpytest_subprocess`, which is also the only mode
   that exercises the entry point honestly.
7. **Timing belongs around the `yield`.** Measuring inside the hook body
   measures the hook. Wrapping the yield measures the phase, including the
   other hooks that ran for it.
8. **Milliseconds, not seconds.** `0.312` and `0.401` read as the same number at
   a glance; `312.400` and `401.310` do not.
9. **Write the file in `pytest_sessionfinish`.** An `atexit` hook runs after the
   interpreter has started tearing down and has no exit status to record.

## Layout

| path | what it is |
| ---- | ---------- |
| `src/{{ package_name }}/plugin.py` | the hooks: options, marker, recorder, strict mode |
| `src/{{ package_name }}/model.py` | the report format, validated on the way in |
| `src/{{ package_name }}/cli.py` | `summary`, the duration gate, exit codes |
| `src/{{ package_name }}/selftest.py` | offline checks that need no pytest session |
| `fixtures/demo/` | a ticketed project, plus one file with no ticket to refuse |
