# {{ npm_name }}

A key/value store that keeps every write in an append-only log before it
answers. The map in memory is a cache of the log; restart the process and the
same bytes come back.

```
PUT    /kv/<key>      store the request body (<= 64 KiB), 201
GET    /kv/<key>      the stored bytes, 404 when absent
DELETE /kv/<key>      204, or 404 when it was never there
GET    /health        {"status":"ok","keys":N}
GET    /wal           segment, record and byte counts
POST   /compact       rewrite the live keys into one fresh segment
```

## Layout

| Path | Role |
| --- | --- |
| `wal.go` | record framing: length, CRC32C, op, key, value |
| `store.go` | replay, put/delete, compaction, statistics |
| `handler.go` | the HTTP contract, including the 413 and 405 bodies |
| `server.go` | listener, graceful `Shutdown`, `PORT` parsing |
| `selftest.go` | 83 checks over a real listener |
| `smoke.sh` | the same contract through `curl` and a restart |

## Run it

```
make build
./bin/{{ npm_name }} --dir wal --addr 127.0.0.1:5491
curl -X PUT --data-binary hello http://127.0.0.1:5491/kv/greeting
```

## Traps this starter already paid for

- A record is only durable once `Sync` returns; write the frame and fsync it
  *before* mutating the in-memory map, or a crash answers 201 for a value that
  never reached the disk.
- `io.ReadFull` reports a short header as `io.ErrUnexpectedEOF`, not as your own
  torn-record error. Map everything except a clean zero-byte `io.EOF` to the torn
  case, or the replayer returns a bare `unexpected EOF` and the truncation branch
  never runs.
- Only the LAST segment may hold a torn tail. A torn record in a sealed segment
  means the log is inconsistent, and silently truncating it hides corruption.
- Truncate with `os.Truncate(path, size-discarded)`. Collecting the good prefix in
  memory and rewriting the file also works, but then a crash mid-rewrite loses
  records that were durable a moment earlier.
- Compaction writes `wal-<next>.log.tmp`, fsyncs, and renames. The rename is the
  commit point, so `segmentIndexes` must ignore `.tmp` files — otherwise a
  half-written segment is replayed next boot.
- A delete needs a tombstone record, not just a map delete: a log that only
  records puts resurrects deleted keys on the next replay.
- CRC the whole payload, not the header: the length prefix is what a partial write
  damages, and the checksum is what tells a torn tail apart from a corrupt one.
- `parsePort` must reject `""`, `-1` and `70000`; `strconv.Atoi` happily accepts a
  negative number and `net.Listen` then panics later with a confusing message.
