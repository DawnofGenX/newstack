# Stack Quality Bar

Every stack under `src/newstack/data/stacks/<name>/` must ship an executable proof
of life inside its `template/` directory. The bar is enforced by
`tests/test_stack_bar.py`.

## What counts

- `template/smoke.sh` exists and is executable. It runs the generated project's
  real entry point (build/run/assert output) with `set -e` semantics and exits
  non-zero on any failure. No network, no privileged ports, no long installs.
- For Python stacks (`stack.is_python`), `template/**/selftest.py` exists **or**
  the stack is listed in `docs/bar-exceptions.json`.
- `template/README.md` exists.

## Exceptions

`docs/bar-exceptions.json` maps a stack name to a one-line reason. It is an
allowlist for Python stacks where a `selftest.py` is not meaningful (doc sites
and web apps, whose proof is a request/render script run under pytest). Rules:

- Every key must name a stack that exists in the registry.
- No key may name a stack that already ships `selftest.py`.
- No key may name a stack that is not Python.

The test asserts all three.