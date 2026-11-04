# {{ project_name }}

{{ description }}

A small HTTP service with everything around it that makes it runnable: a
container image, a compose file with a real healthcheck, a Makefile, and two
layers of tests — unit tests that need nothing, and a smoke test that starts a
real container and asks it real questions.

## Endpoints

| path | answer |
| --- | --- |
| `/` | service name, version, endpoint list |
| `/health` | `{"service": …, "status": "ok", "version": …}` — what the container healthcheck polls |
| `/metrics` | Prometheus text: `requests_total`, `uptime_seconds` |

Anything else is `404` naming the path; a non-`GET` method is `405`.

## Run it

```bash
make test     # unit tests, no Docker, no network
make up       # build and start, wait until healthy
curl -s localhost:8080/health
make down
```

`make smoke` does all of that on port 18080 and asserts each answer, then
removes the container whether the checks passed or failed. `make logs` follows
the container's output.

## Layout

```
app/service.py    the contract: build_reply(path, state) -> Reply, pure functions
app/server.py     the only file that touches a socket
tests/            unit tests for the contract, smoke test for the container
Dockerfile        python:3.12-slim, non-root uid 10001, HEALTHCHECK
docker-compose.yml  one service, PORT from the environment, restart unless-stopped
Makefile          help / build / up / down / smoke / test / logs
```

The split matters: because the answers live in `service.py`, the interesting
part is testable without Docker, and the container test only has to prove that
the wiring (port, healthcheck, image) is right.

## Configuration

| variable | default | meaning |
| --- | --- | --- |
| `PORT` | `8080` | host port published by compose |
| `LOG_REQUESTS` | `1` | set to `0` to silence the access log |

Copy `.env.example` to `.env` and compose will pick it up.
