"""Tests for the wire format, the zone and both transports."""

from __future__ import annotations

import struct

import pytest

from {{ package_name }}.client import (
    ask_tcp,
    ask_udp,
    build_query,
    parse_reply,
)
from {{ package_name }}.protocol import (
    CLASS_IN,
    FORMERR,
    NXDOMAIN,
    REFUSED,
    TYPE_A,
    TYPE_AAAA,
    TYPE_ANY,
    TYPE_CNAME,
    TYPE_TXT,
    FormatError,
    encode_name,
    parse_query,
    read_name,
    read_utf8_rdata,
)
from {{ package_name }}.server import Server, parse_port, respond
from {{ package_name }}.zone import demo_zone, txt

HOST = "127.0.0.1"


@pytest.fixture()
def server():
    running = Server(HOST, 0, zone=demo_zone("example.test")).start()
    try:
        yield running
    finally:
        running.shutdown()


def query_over_udp(server: Server, name: str, qtype: int = TYPE_A, **options: int):
    reply = ask_udp(HOST, server.port, build_query(name, qtype, **options))
    return parse_reply(reply)


def test_a_name_round_trips():
    assert read_name(encode_name("deep.www.example.test"), 0)[0] == "deep.www.example.test"


def test_the_root_name_is_one_zero_byte():
    assert encode_name(".") == b"\x00"
    assert read_name(b"\x00", 0) == (".", 1)


def test_a_pointer_is_followed_without_moving_the_cursor_past_the_pointer():
    packet = b"\x07example\x04test\x00\x03ns1\xc0\x00"
    assert read_name(packet, 14) == ("ns1.example.test", 20)


def test_a_forward_pointer_is_a_format_error():
    with pytest.raises(FormatError, match="backwards"):
        read_name(b"\x03www\xc0\x0a", 0)


def test_a_pointer_loop_is_cut_off():
    with pytest.raises(FormatError):
        read_name(b"\x01a\xc0\x00" + b"\x00" * 4, 0)


def test_an_overlong_label_is_rejected():
    with pytest.raises(FormatError, match="bad label"):
        encode_name("x" * 64 + ".example.test")


def test_a_query_is_parsed_with_its_question():
    parsed = parse_query(build_query("www.example.test", TYPE_A, ident=7))
    assert parsed.ident == 7
    assert parsed.question.name == "www.example.test"
    assert parsed.question.qtype == TYPE_A
    assert parsed.question.qclass == CLASS_IN


def test_edns0_raises_the_udp_limit():
    assert parse_query(build_query("example.test", TYPE_A)).udp_limit == 512
    assert parse_query(build_query("example.test", TYPE_A, edns=4096)).udp_limit == 4096


def test_a_packet_without_a_question_is_a_format_error():
    with pytest.raises(FormatError):
        parse_query(struct.pack("!HHHHHH", 1, 0, 0, 0, 0, 0))


def test_txt_rdata_is_length_prefixed_chunks():
    raw = txt("x" * 300)
    assert raw[0] == 255
    assert raw[256] == 45
    assert read_utf8_rdata(raw) == "x" * 300


def test_the_zone_answers_a_records_in_insertion_order(server):
    reply = query_over_udp(server, "www.example.test")
    assert reply.texts() == ["192.0.2.11", "192.0.2.12"]
    assert reply.authoritative
    assert reply.ident == 0x1234


def test_the_zone_answers_aaaa_and_txt(server):
    assert query_over_udp(server, "example.test", TYPE_AAAA).texts() == ["2001:db8::10"]
    assert query_over_udp(server, "example.test", TYPE_TXT).texts() == ["v=spf1 -all"]


def test_a_cname_is_included_then_followed(server):
    reply = query_over_udp(server, "alias.example.test")
    assert reply.answers[0].rtype == TYPE_CNAME
    assert reply.texts() == ["www.example.test", "192.0.2.11", "192.0.2.12"]


def test_any_returns_every_record_at_the_name(server):
    reply = query_over_udp(server, "www.example.test", TYPE_ANY)
    assert len(reply.answers) == 2


def test_an_unknown_name_is_nxdomain_with_the_soa(server):
    reply = query_over_udp(server, "nope.example.test")
    assert reply.rcode == NXDOMAIN
    assert reply.authoritative
    assert [record.rtype for record in reply.authority] == [6]
    assert reply.answers == []


def test_a_missing_type_is_noerror_with_the_soa(server):
    reply = query_over_udp(server, "www.example.test", TYPE_TXT)
    assert reply.rcode == 0
    assert [record.rtype for record in reply.authority] == [6]


def test_a_name_outside_the_zone_is_refused(server):
    reply = query_over_udp(server, "example.org")
    assert reply.rcode == REFUSED
    assert not reply.authoritative


def test_the_transaction_id_is_echoed(server):
    reply = query_over_udp(server, "www.example.test", ident=0xABCD)
    assert reply.ident == 0xABCD


def test_a_big_answer_is_truncated_over_udp(server):
    reply = query_over_udp(server, "big.example.test", TYPE_TXT)
    assert reply.truncated
    assert reply.answers == []


def test_edns0_lets_the_big_answer_through(server):
    reply = query_over_udp(server, "big.example.test", TYPE_TXT, edns=4096)
    assert not reply.truncated
    assert len(reply.texts()[0]) == 510


def test_tcp_carries_the_whole_answer(server):
    payload = ask_tcp(HOST, server.port, build_query("big.example.test", TYPE_TXT))
    reply = parse_reply(payload)
    assert not reply.truncated
    assert len(reply.texts()[0]) == 510


def test_a_two_byte_packet_is_dropped():
    assert respond(b"\x12\x34", demo_zone()) == b""


def test_a_truncated_question_gets_formerr():
    packet = b"\x12\x34\x01\x00\x00\x01" + b"\x00" * 6 + b"\x03www"
    reply = parse_reply(respond(packet, demo_zone()))
    assert reply.rcode == FORMERR
    assert reply.ident == 0x1234


def test_two_questions_in_one_packet_is_formerr():
    packet = bytearray(build_query("www.example.test", TYPE_A))
    struct.pack_into("!H", packet, 4, 2)
    packet += encode_name("www.example.test") + struct.pack("!HH", TYPE_A, CLASS_IN)
    assert parse_reply(respond(bytes(packet), demo_zone())).rcode == FORMERR


@pytest.mark.parametrize("raw", ["nope", "70000", "-1"])
def test_parse_port_rejects_nonsense(raw):
    with pytest.raises(ValueError):
        parse_port(raw)


def test_shutdown_releases_both_sockets():
    server = Server(HOST, 0, zone=demo_zone()).start()
    port = server.port
    server.shutdown()
    with pytest.raises(OSError):
        ask_udp(HOST, port, build_query("example.test"), timeout=1.0)
