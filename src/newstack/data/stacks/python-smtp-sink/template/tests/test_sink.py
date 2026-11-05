"""Talk SMTP to the sink the way a real client does."""

from __future__ import annotations

import json
import smtplib
import socket
from email.message import EmailMessage

import pytest

from {{ package_name }}.mailbox import Mailbox, subject_of
from {{ package_name }}.server import Sink, SinkConfig


@pytest.fixture()
def sink(tmp_path):
    mailbox = tmp_path / "mailbox"
    server = Sink(SinkConfig(port=0, root=mailbox, size_limit=8192)).start()
    try:
        yield server
    finally:
        server.stop()


def send(port: int, message: EmailMessage, mail_from: str, rcpt: list[str], **kwargs) -> None:
    with smtplib.SMTP("127.0.0.1", port, timeout=10) as client:
        client.ehlo()
        client.send_message(message, from_addr=mail_from, to_addrs=rcpt, **kwargs)


def build(subject: str = "hello", body: str = "one\ntwo\n") -> EmailMessage:
    message = EmailMessage()
    message["From"] = "writer@example.test"
    message["To"] = "reader@example.test"
    message["Subject"] = subject
    message.set_content(body)
    return message


def test_a_message_is_stored_and_indexed(sink):
    send(sink.port, build(), "writer@example.test", ["reader@example.test"])
    messages = sink.mailbox.messages()
    assert len(messages) == 1
    stored = messages[0]
    assert stored.sender == "writer@example.test"
    assert stored.recipients == ("reader@example.test",)
    assert stored.subject == "hello"
    assert stored.size > 0
    assert (sink.mailbox.root / stored.path).exists()


def test_the_stored_bytes_are_the_received_bytes(sink):
    send(sink.port, build(body="alpha\nbeta\n"), "writer@example.test", ["reader@example.test"])
    stored = sink.mailbox.messages()[0]
    raw = (sink.mailbox.root / stored.path).read_bytes()
    assert b"alpha\r\nbeta" in raw or b"alpha\nbeta" in raw
    assert len(raw) == stored.size


def test_a_line_starting_with_a_dot_survives_dot_stuffing(sink):
    body = ".hidden\n..two\nnormal\n"
    send(sink.port, build(body=body), "writer@example.test", ["reader@example.test"])
    raw = (sink.mailbox.root / sink.mailbox.messages()[0].path).read_bytes()
    # Dot-stuffing is a wire encoding: the client adds a dot, the server removes
    # it, and the payload the sender wrote is what must come back. A raw scan
    # for ".." cannot prove that -- parse the stored message instead.
    from email.parser import BytesParser

    parsed = BytesParser().parsebytes(raw)
    payload = parsed.get_payload(decode=True)
    assert payload == body.replace("\n", "\r\n").encode()


def test_two_recipients_are_recorded(sink):
    send(sink.port, build(), "writer@example.test", ["a@example.test", "b@example.test"])
    assert sink.mailbox.messages()[0].recipients == ("a@example.test", "b@example.test")


def test_utf8_headers_and_bodies_are_accepted(sink):
    message = EmailMessage()
    message["From"] = "\u00e9crivain@example.test"
    message["To"] = "reader@example.test"
    message["Subject"] = "caf\u00e9 r\u00e9sum\u00e9"
    message.set_content("h\u00e9llo w\u00f6rld\n")
    send(
        sink.port,
        message,
        "\u00e9crivain@example.test",
        ["reader@example.test"],
        mail_options=["SMTPUTF8"],
    )
    stored = sink.mailbox.messages()[0]
    assert "caf\u00e9" in stored.subject
    assert "h\u00e9llo".encode() in (sink.mailbox.root / stored.path).read_bytes()


def test_an_oversized_message_is_refused_by_the_server(sink):
    message = build(body="x" * 20000)
    # With EHLO SIZE advertised, the refusal can come at MAIL FROM; without it,
    # at DATA. Both are 552 and both mean the message never reached the handler.
    with pytest.raises((smtplib.SMTPDataError, smtplib.SMTPSenderRefused)) as caught:
        send(sink.port, message, "writer@example.test", ["reader@example.test"])
    assert caught.value.smtp_code == 552
    assert sink.mailbox.count() == 0


def test_a_rejected_recipient_is_refused(tmp_path):
    server = Sink(
        SinkConfig(port=0, root=tmp_path / "mailbox", reject_recipients=("bounce@example.test",))
    ).start()
    try:
        with smtplib.SMTP("127.0.0.1", server.port, timeout=10) as client:
            client.ehlo()
            with pytest.raises(smtplib.SMTPDataError) as caught:
                client.send_message(
                    build(), from_addr="writer@example.test", to_addrs=["bounce@example.test"]
                )
        assert caught.value.smtp_code == 550
        assert server.mailbox.count() == 0
        assert server.handler.refused
    finally:
        server.stop()


def test_the_sink_answers_ehlo_with_size(sink):
    with smtplib.SMTP("127.0.0.1", sink.port, timeout=10) as client:
        code, message = client.ehlo()
        assert code == 250
        assert b"SIZE" in message


def test_the_mailbox_survives_a_restart(sink, tmp_path):
    send(sink.port, build(subject="first"), "writer@example.test", ["reader@example.test"])
    sink.stop()
    reopened = Mailbox(sink.mailbox.root)
    assert reopened.count() == 1
    assert reopened.messages()[0].subject == "first"


def test_a_torn_index_line_is_ignored(tmp_path):
    mailbox = Mailbox(tmp_path / "mailbox")
    mailbox.store("writer@example.test", ["reader@example.test"], b"Subject: ok\r\n\r\nbody")
    with mailbox.index_path.open("a", encoding="utf-8") as handle:
        handle.write('{"id": "unfinished"')
    assert mailbox.count() == 1


def test_the_index_can_be_rebuilt_from_the_files(tmp_path):
    mailbox = Mailbox(tmp_path / "mailbox")
    stored = mailbox.store(
        "writer@example.test", ["reader@example.test"], b"Subject: kept\r\n\r\nbody"
    )
    mailbox.index_path.unlink()
    assert mailbox.rebuild_index() == 1
    rebuilt = mailbox.messages()
    assert len(rebuilt) == 1
    assert rebuilt[0].sha256 == stored.sha256
    assert rebuilt[0].subject == "kept"


def test_subject_decoding_handles_a_folded_header():
    raw = b"Subject: a very long\r\n subject line\r\nX-Other: 1\r\n\r\nbody"
    assert subject_of(raw) == "a very long subject line"


def test_a_message_without_a_subject_is_fine():
    assert subject_of(b"From: a@b\r\n\r\nbody") == ""


def test_the_cli_lists_what_is_in_the_mailbox(tmp_path, capsys):
    from {{ package_name }} import cli

    root = tmp_path / "mailbox"
    mailbox = Mailbox(root)
    mailbox.store("writer@example.test", ["reader@example.test"], b"Subject: listed\r\n\r\nbody")
    assert cli.main(["list", "--mailbox", str(root)]) == 0
    printed = capsys.readouterr().out
    assert "writer@example.test" in printed
    assert "subject: listed" in printed

    assert cli.main(["list", "--mailbox", str(root), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload[0]["subject"] == "listed"


def test_the_port_is_the_bound_one_and_not_the_requested_zero(sink):
    with socket.create_connection(("127.0.0.1", sink.port), timeout=5) as client:
        client.settimeout(5)
        assert client.recv(64).startswith(b"220")
