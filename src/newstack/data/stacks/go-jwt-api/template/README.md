# blog-count as a token service

A JSON API that keeps accounts and issues bearer tokens. No framework, no module
dependencies: `net/http`, `crypto/hmac`, and a hand-written PBKDF2.

    make build
    TOKEN_SECRET=dev-secret PORT=8080 ./build/blog-count --db users.json

## Routes

| Method | Path        | Answers                                                        |
| ------ | ----------- | -------------------------------------------------------------- |
| GET    | `/health`   | `{"status":"ok","users":N}`                                     |
| POST   | `/register` | 201 `{"id":1,"email":"..."}`; 409 `email_taken`; 422 on bad input |
| POST   | `/login`    | 200 `{"token":"...","token_type":"Bearer","expires_at":...}`     |
| GET    | `/me`       | 200 `{"id","email","issued_at","expires_at"}` behind a bearer   |

Errors are always `{"error": "...", "detail": "..."}`. Every rejected token is a
401 `invalid_token`, and a wrong password is indistinguishable from an unknown
account.

## Layout

    token.go        issue/verify HMAC-SHA256 tokens, bearer parsing
    password.go     PBKDF2-HMAC-SHA256 digests, constant-time comparison
    store.go        in-memory accounts with an atomic JSON file behind them
    handlers.go     the routing table and the response shapes
    server.go       net/http with a graceful stop
    selftest.go     62 in-process checks, `--selftest`
    handlers_test.go go test: live httptest server, expiry, enumeration, restart

## Traps this starter already paid for

- **A token carries its deadline, not its lifetime.** `exp` is an absolute
  timestamp; a stored duration would have to be read against the issuer's clock
  and a restarted verifier would guess.
- **Compare signatures with `hmac.Equal`, passwords with
  `subtle.ConstantTimeCompare`.** `==` on a MAC or a digest returns early on the
  first wrong byte, which is enough to recover the rest one byte at a time.
- **The digest records its own parameters** (`pbkdf2-sha256$120000$salt$key`).
  Raising the iteration count later must not invalidate every stored password.
- **An unknown email still hashes.** `login` verifies against a dummy digest when
  no account matches, so "no such user" is not measurably faster than "wrong
  password". Returning a different error is the same leak with fewer steps.
- **`/me` looks the account up.** Claims alone would keep a deleted account's
  token alive forever; the store is the authority.
- **Pointers in the request struct.** `Email *string` distinguishes an absent
  field from `""`, so a client that forgot `password` gets `missing_password`
  rather than a confusing `weak_password`.
- **The store refuses to open a corrupt file.** Starting empty and then saving
  would silently erase every account on the next signup.
- **`Save` writes a temp file and renames.** An in-place write leaves a truncated
  JSON file if the process dies mid-write, and the next boot would refuse it.
- **The port has to be released, not just signalled.** The step traps EXIT,
  sends TERM, waits, and only then cleans up, so the next run does not inherit a
  listener.
