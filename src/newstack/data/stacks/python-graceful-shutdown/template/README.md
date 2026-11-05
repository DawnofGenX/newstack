# {{ title }}

A stdlib HTTP server whose shutdown is the interesting part. A deploy sends
`SIGTERM`; the process must stop accepting, finish the requests it already took, and
only then exit with a code the orchestrator can trust.

```
$ .venv/bin/python -m {{ package_name }} serve --port 5477 --drain-timeout 10
listening 127.0.0.1:5477
signal 15: draining 1 request(s)
drained 1 request(s) in 0.71s
stopped
$ echo $?
0
```

## Quick start

```bash
uv venv && uv pip install --python .venv/bin/python -e . pytest ruff
.venv/bin/python -m {{ package_name }} serve --port 5477 &
.venv/bin/python -m pytest
PY=.venv/bin/python bash smoke.sh
```

| Signal | Behaviour | Exit |
| --- | --- | --- |
| `SIGTERM`/`SIGINT`, nothing in flight | listener closed, process stops | `0` |
| `SIGTERM`/`SIGINT`, requests in flight | they finish, then the process stops | `0` |
| in-flight work passes `--drain-timeout` | give up, report the count | `1` |
| a second signal | `os._exit(130)` immediately | `130` |

`GET /health` is readiness, not liveness: `200 ok` while running, `503 draining` once
the drain has begun, so a load balancer takes the process out before it disappears.

## The traps this template exists to expose

1. **Daemon request threads.** `ThreadingHTTPServer` sets `daemon_threads = True`, so
   the interpreter exits underneath a response that is still being written. The client
   sees a truncated body and no error anywhere. This template sets it to `False` and
   waits on a clock instead of on `server_close()`.
2. **`shutdown()` deadlocks on the serving thread.** It blocks until `serve_forever()`
   returns, so calling it from inside the loop waits for a loop that is waiting for it.
   The drain watcher is a separate thread; the signal handler only flips state.
3. **`shutdown()` leaves the listening socket open.** New clients connect happily and
   then wait forever. The listener is closed explicitly, so the next connect is refused.
4. **Keep-alive connections outlive the listener.** A connection opened a second before
   the signal can carry a brand-new request. It is answered `503` with
   `Connection: close` and *not* counted as in-flight, or the drain finishes, the process
   exits, and that request is reset mid-flight.
5. **A second signal must win.** Deploy tooling sends another `SIGTERM` when it is
   impatient; swallowing it produces a process that survives `kill` and a stuck rollout.
6. **A hung request must not hang the deploy.** The drain is bounded, hitting the bound
   is exit code `1`, not `0` (a clean exit would hide the abandoned work), and the
   process leaves *immediately*: `server_close()` would join the very threads that blew
   the deadline, so a "timeout" that waits for them is decoration.
7. **Buffered output hides the evidence.** Every lifecycle line is printed with
   `flush=True`; without it the last lines are lost exactly when you need them, and the
   `os._exit(130)` path does not run the flush that `sys.exit()` would.
8. **`KeyboardInterrupt` is `SIGINT`.** Handling `SIGTERM` and leaving `SIGINT` to the
   interpreter means Ctrl-C skips the drain entirely. Both are wired to the same path.

## Layout

```
src/{{ package_name }}/lifecycle.py   running -> draining -> stopped, admitted/released counts
src/{{ package_name }}/service.py     the handler, the server, the signal wiring
tests/test_lifecycle.py              the state machine with no sockets
tests/test_signals.py                real processes: SIGTERM in flight, double signal, timeout
smoke.sh                             the same story through bash, with exit codes
```
