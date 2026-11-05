# blog-count as an upload service

Resumable uploads with nothing but `node:http`, `node:fs` and `node:crypto`.
The client declares the name and the total size, then sends byte ranges; the
service refuses an offset that does not match what it already has, and answers
the last chunk with a SHA-256 of the whole file.

    UPLOAD_DIR=uploads PORT=8080 node src/main.js

## Routes

| Method | Path                     | Answers                                                     |
| ------ | ------------------------ | ----------------------------------------------------------- |
| GET    | `/health`                | `{"status":"ok","sessions":N}`                               |
| POST   | `/uploads`               | 201 `{"id","name","size","received":0,"offset":0}`           |
| PUT    | `/uploads/{id}?offset=N` | 200 progress, or `complete` + `sha256` on the last byte      |
| GET    | `/uploads/{id}`          | 200 status; 404 `unknown_upload`                             |
| GET    | `/uploads/{id}/content`  | 200 bytes when complete, else 409 `incomplete`               |
| DELETE | `/uploads/{id}`          | 204, and the bytes are gone                                  |

## Layout

    src/store.js    one file per upload, an index written atomically, SHA-256
    src/routes.js   the routing table, the body caps, the offset check
    src/server.js   node:http, timeouts, and a stop that does not hang
    src/main.js     UPLOAD_DIR / HOST / PORT, signal handling
    tests/routes.test.js  12 tests against a real server on port 0

## Traps this starter already paid for

- **The offset is the client's claim, not a fact.** `PUT` with an offset that is
  not `received` is a 409 with the expected value: accepting it would drop or
  duplicate bytes, and the file would still pass a length check while being
  wrong.
- **Rebuild the hash before writing the next chunk.** The running hash cannot be
  serialised, so after a restart it is rebuilt from the file — and a rebuild that
  runs *after* the new bytes land hashes them twice and reports a digest no
  client can reproduce.
- **Write at the recorded offset, not at the end.** `fs.appendFile` would happily
  glue a replayed chunk onto the file; a positional `handle.write` cannot.
- **Cap the body while it streams.** `Content-Length` is the client's promise,
  and a request that sends nothing at all can still make a trusting server
  allocate the declared size.
- **The index is written with a temp file and a rename.** A truncated
  `sessions.json` is not a smaller truth: the next boot has no idea how many
  bytes are on disk and cannot safely resume.
- **`server.close()` alone does not stop the process.** It waits for keep-alive
  sockets to drain, so `stop()` calls `closeIdleConnections()` and gives the rest
  two seconds before `closeAllConnections()`.
- **204 sends no body.** `res.end()` with no payload and no `Content-Length` is
  the only correct answer to a delete, and clients that read one get confused.
- **A thrown handler still has to answer.** `route()` wraps everything in a
  `try/catch`; an unhandled rejection otherwise leaves the socket hanging until
  the client times out.
