# {{ title }}

A dependency-free solver keeps its function, its stopping rule and its error
reporting separate, so every refusal names the condition that caused it.

## Usage

```sh
make
./bin/{{ npm_name }} 2 3
# root=2.0945514815 iterations=31

./bin/{{ npm_name }} --tol 0.001 --iter 100 2 3
make test
```

The interval must bracket a root: `f(lo)` and `f(hi)` have opposite signs.
`--tol` (default 1e-9) stops when half the remaining bracket is small enough;
`--iter` (default 200) is a hard budget. Exit status is 0 on success, 1 on a
solver error and 2 on a usage error.

## Layout

- `src/root_find.f90` — bisection with an injected pure function
- `src/root_options.f90` — hand-written option parser
- `src/root_runner.f90` — CLI boundary with injected output units
- `tests/run_tests.f90` — dependency-free assertions
