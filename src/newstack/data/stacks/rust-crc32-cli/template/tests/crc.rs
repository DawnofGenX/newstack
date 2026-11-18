use {{ package_name }}::{Crc32, crc32, crc32c, to_hex};

#[test]
fn ieee_check_value() {
    // The CRC-32 check value every specification pins down.
    assert_eq!(crc32(b"123456789"), 0xCBF4_3926);
    assert_eq!(to_hex(crc32(b"123456789")), "cbf43926");
}

#[test]
fn empty_input_is_zero() {
    assert_eq!(crc32(b""), 0x0000_0000);
}

#[test]
fn castagnoli_check_value() {
    assert_eq!(crc32c(b"123456789"), 0xE306_9283);
}

#[test]
fn incremental_updates_match_one_shot() {
    let payload = b"the quick brown fox jumps over the lazy dog";
    let mut crc = Crc32::ieee();
    crc.update(&payload[..10])
        .update(&payload[10..27])
        .update(&payload[27..]);
    assert_eq!(crc.finish(), crc32(payload));
}

#[test]
fn finish_is_idempotent() {
    let mut crc = Crc32::ieee();
    crc.update(b"abc");
    assert_eq!(crc.finish(), crc.finish());
}

#[test]
fn known_payload_matches_python() {
    // Python: binascii.crc32(b"hello world") == 222957957
    assert_eq!(crc32(b"hello world"), 0x0D4A_1185);
}
