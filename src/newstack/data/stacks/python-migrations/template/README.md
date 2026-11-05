# {{ title }}

Forward-only SQL migrations for SQLite, with a ledger that can prove a file changed.

```
{{ npm_name }} status   # every file, and what the ledger says about it
{{ npm_name }} up       # apply what is pending
{{ npm_name }} verify   # exit 1 if an applied file was edited
```

`--db app.db` and `--dir migrations` are the defaults.

## The three rules

**An applied file that changed is drift, and nothing runs.** The ledger stores the
sha256 of the bytes that ran, so a reworded comment, a re-indented statement or a
missing trailing newline is enough to be told about it. The alternative — trusting
"0002 already ran" — is a database that matches neither the file nor the ledger,
and no way to know which.

**A pending migration older than the newest applied one is refused.** Applying it
late gives an existing database a different schema history than a fresh one built
from the same directory. Both look fine on their own, which is what makes it the
worst kind of difference.

**A migration is one transaction.** Not one per statement, and not
`executescript`: that call commits any open transaction before it starts, so the
`with connection:` you wrapped around it rolls nothing back.

## Why the splitter uses SQLite's parser

Splitting a file on `;` looks fine until a statement contains a semicolon: inside
a string literal, inside a `BEGIN … END` trigger body, or in a comment. The
resulting fragments are not a syntax error you will see at review time — they run
half a migration. `sqlite3.complete_statement()` asks SQLite's own parser whether
the buffer so far is a complete statement, which is the only splitter that knows
the grammar:

```python
for line in sql.splitlines(keepends=True):
    buffer += line
    if sqlite3.complete_statement(buffer):
        statements.append(buffer.strip())
        buffer = ""
```

## Why every migration opens its own transaction

The `sqlite3` module's default isolation level opens a transaction before
`INSERT`/`UPDATE`/`DELETE` — and never around DDL. So this does **not** roll back:

```python
with sqlite3.connect("app.db") as db:      # commits on exit, rolls back on error…
    db.execute("CREATE TABLE a (x)")       # …but this was already committed
    db.execute("CREATE TABLE a (x)")       # error: table a already exists
```

`tests/test_runner.py` keeps a test that records that behaviour, so the runner
cannot be "simplified" back into it. `store.connect()` therefore passes
`isolation_level=None` and `runner.apply()` writes `BEGIN` / `COMMIT` /
`ROLLBACK` itself.

## Adding a migration

```
migrations/0004_add_tags.sql
```

The id is in the filename so that `ls` shows the order. Gaps are allowed — a
migration reverted before it shipped leaves one behind, and refusing to start
would punish history. Duplicates are not: two files that claim the same position
cannot both be second.

## Exit codes

| code | meaning |
| --- | --- |
| 0 | the database matches the repository |
| 1 | drift: a file changed after it was applied, so a human must decide |
| 2 | unusable: bad filename, duplicate id, failing SQL, missing directory |
