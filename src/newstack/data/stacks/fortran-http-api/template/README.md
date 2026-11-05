# {{ title }}

{{ description }}

Fortran's standard library has no sockets, so `server_m.f90` declares
`socket`, `bind`, `listen`, `accept`, `recv`, `send` and `close` as
`bind(c)` interfaces and speaks HTTP/1.1 over an `int8` buffer. `counts_m.f90`
counts lines, words and bytes, `json_m.f90` is a recursive-descent reader that keeps only the
`text` member (decoding `\u` escapes and surrogate pairs into UTF-8), and
`contract_m.f90` holds the routes as one pure subroutine.

## Layout

```
Makefile                 gfortran -Wall -Wextra -Werror, one binary
src/bytes_m.f90          growable int8 buffer + ASCII helpers
src/counts_m.f90         lines / words / bytes over raw bytes
src/json_m.f90           recursive-descent JSON reader, escapes, surrogate pairs
src/contract_m.f90       routes, percent decoding, JSON writer
src/server_m.f90         libc sockets via ISO_C_BINDING, one request at a time
src/main.f90             --selftest, PORT, exit codes
tests/selftest_m.f90     38 checks, no framework
bin/{{ npm_name }}             build and run
.github/workflows/ci.yml build, self test, HTTP contract
```

## Run

```sh
make test
PORT=8080 ./bin/{{ npm_name }}
curl -s 'http://127.0.0.1:8080/stats?text=hello%20world%0A'
```

## Traps this starter already paid for

- A Fortran character constant has no escape sequences: `'\n'` is a backslash
  and an `n` (which is exactly what JSON wants on the way in), and a real newline
  is `char(10)`. Mixing the two silently produces the wrong body.
- `size` is an intrinsic, so it cannot be a dummy argument name.
- `c_loc` requires the TARGET attribute; a component of a derived type does not
  have it, so the response is copied into a local `target` array before `c_send`.
- `sockaddr_in` is built byte by byte instead of declared as a derived type: no
  struct layout or padding to guess, and the port is placed in network order by
  hand.
- `append`-style helpers need `move_alloc`, not `a = b` on allocatables that are
  already allocated.
