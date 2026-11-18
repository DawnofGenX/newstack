use {{ package_name }}::{decode, encode};

#[test]
fn rfc4648_vector() {
    assert_eq!(encode(b"foobar", false, true), "Zm9vYmFy");
}

#[test]
fn round_trip() {
    let enc = encode(b"hello world", false, true);
    let dec = decode(&enc, false).unwrap();
    assert_eq!(dec, b"hello world");
}

#[test]
fn bad_input_is_error() {
    assert!(decode("!!!!", false).is_err());
}

#[test]
fn url_safe_round_trip() {
    let enc = encode(b"hello world", true, false);
    assert!(!enc.contains('+') && !enc.contains('/'));
    let dec = decode(&enc, true).unwrap();
    assert_eq!(dec, b"hello world");
}
