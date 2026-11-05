#!/usr/bin/env bash
# Drive the sink the way a mail client and a developer do: SMTP in, CLI out.
set -euo pipefail

cd "$(dirname "$0")"
PY=${PY:-.venv/bin/python}
PORT=${PORT:-5482}

work=$(mktemp -d)
server=""
stop() {
    if [ -n "$server" ]; then
        kill -TERM "$server" 2>/dev/null || true
        for _ in $(seq 1 20); do kill -0 "$server" 2>/dev/null || break; sleep 0.1; done
        kill -KILL "$server" 2>/dev/null || true
        wait "$server" 2>/dev/null || true
    fi
    rm -rf "$work"
}
trap stop EXIT

if "$PY" - "$PORT" 2>/dev/null <<'PY'
import socket
import sys

sock = socket.create_connection(("127.0.0.1", int(sys.argv[1])), timeout=1)
sock.close()
PY
then
    echo "port $PORT is already answering - stop that process before running this step" >&2
    exit 1
fi

"$PY" -m {{ package_name }}.cli serve --port "$PORT" --mailbox "$work/mailbox" \
    --size-limit 2048 --reject bounce@example.test >"$work/server.log" 2>&1 &
server=$!

for _ in $(seq 1 160); do
    if "$PY" - "$PORT" 2>/dev/null <<'PY'
import socket
import sys

sock = socket.create_connection(("127.0.0.1", int(sys.argv[1])), timeout=1)
sock.close()
PY
    then
        break
    fi
    sleep 0.25
done
kill -0 "$server"

# The client below is a plain smtplib client: nothing from the project is
# imported, so a bug in the sink's own idea of SMTP cannot hide here.
"$PY" - "$PORT" "$work/mailbox" <<'PY'
import json
import pathlib
import smtplib
import sys
from email.message import EmailMessage

port, mailbox = int(sys.argv[1]), pathlib.Path(sys.argv[2])
checks = 0


def ok(name):
    global checks
    checks += 1
    print(f"ok {name}")


def fail(name, detail):
    print(f"FAIL {name}: {detail}", file=sys.stderr)
    raise SystemExit(1)


def message(subject, body, sender="writer@example.test"):
    note = EmailMessage()
    note["From"] = sender
    note["To"] = "reader@example.test"
    if subject is not None:
        note["Subject"] = subject
    note.set_content(body)
    return note


def send(note, sender="writer@example.test", rcpt=("reader@example.test",), options=()):
    with smtplib.SMTP("127.0.0.1", port, timeout=10) as client:
        client.ehlo()
        return client.send_message(note, from_addr=sender, to_addrs=list(rcpt), mail_options=list(options))


send(message("first mail", "alpha\nbeta\n"))
ok("a message was accepted")

send(message(None, "no subject here\n"))
ok("a message without a subject was accepted")

send(message("two readers", "hello\n"), rcpt=("a@example.test", "b@example.test"))
ok("a message with two recipients was accepted")

ci = message("caf\u00e9 r\u00e9sum\u00e9", "h\u00e9llo w\u00f6rld\n", sender="\u00e9crivain@example.test")
send(ci, sender="\u00e9crivain@example.test", options=["SMTPUTF8"])
ok("an 8-bit message with SMTPUTF8 was accepted")

files = sorted(mailbox.glob("*.eml"))
if len(files) != 4:
    fail("four messages were stored", [p.name for p in files])
ok("four .eml files were written")

index = [json.loads(line) for line in (mailbox / "index.ndjson").read_text().splitlines() if line.strip()]
if len(index) != 4:
    fail("the index has four lines", index)
if [entry["subject"] for entry in index][0] != "first mail":
    fail("the first subject", index[0])
if index[1]["subject"] != "":
    fail("a missing subject is stored as an empty string", index[1])
if index[2]["recipients"] != ["a@example.test", "b@example.test"]:
    fail("the recipients of the third message", index[2])
if "caf\u00e9" not in index[3]["subject"]:
    fail("the decoded UTF-8 subject", index[3])

for entry in index:
    raw = (mailbox / entry["path"]).read_bytes()
    if len(raw) != entry["size"]:
        fail(f"the recorded size of {entry['path']}", (len(raw), entry["size"]))
    if not raw.startswith(b"From:") and b"From:" not in raw[:200]:
        fail(f"{entry['path']} does not look like a message", raw[:40])
ok("every index entry matches its file")

# 552: the server refuses before the handler ever sees the message.
try:
    send(message("too big", "x" * 20000))
except (smtplib.SMTPDataError, smtplib.SMTPSenderRefused) as error:
    if error.smtp_code != 552:
        fail("an oversized message is refused with 552", error)
else:
    fail("an oversized message must be refused", "accepted")
ok("an oversized message is refused with 552")

# 550: policy rejects one recipient, the mailbox stays untouched.
before = len(list(mailbox.glob("*.eml")))
try:
    send(message("bounce", "body\n"), rcpt=("bounce@example.test",))
except smtplib.SMTPDataError as error:
    if error.smtp_code != 550:
        fail("a rejected recipient is refused with 550", error)
else:
    fail("a rejected recipient must be refused", "accepted")
if len(list(mailbox.glob("*.eml"))) != before:
    fail("a refused message must not be stored", before)
ok("a rejected recipient is refused with 550 and stores nothing")

print(f"smoke: all {checks} checks passed")
PY

# The CLI is the public way to read the mailbox back.
listing=$("$PY" -m {{ package_name }}.cli list --mailbox "$work/mailbox" --json)
case "$listing" in
    *'"subject": "first mail"'*) echo "ok list --json shows the subject" ;;
    *) echo "FAIL list --json: $listing" >&2; exit 1 ;;
esac

"$PY" -m {{ package_name }}.cli list --mailbox "$work/mailbox" | grep -q 'subject: caf'
echo "ok list decodes the UTF-8 subject"

# The index is a convenience, not the truth: the .eml files are.
rm "$work/mailbox/index.ndjson"
"$PY" -m {{ package_name }}.cli rebuild --mailbox "$work/mailbox" | grep -q 'indexed 4 message'
echo "ok the index can be rebuilt from the files"

stop
server=""

if ss -ltn 2>/dev/null | grep -q ":$PORT "; then
    echo "FAIL port $PORT is still listening" >&2
    exit 1
fi
echo "ok port $PORT was released"

echo "smoke: all checks passed"
