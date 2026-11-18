use {{ package_name }}::parse;

#[test]
fn parses_basic() {
    let input = "a = 1\nb = \"two\"\n";
    let v = parse(input).unwrap();
    assert_eq!(v.to_json(), "{\"a\": 1, \"b\": \"two\"}");
}

#[test]
fn parses_array_and_table() {
    let input = "arr = [1, 2, 3]\n\n[section]\nx = 5\nflag = true\n";
    let v = parse(input).unwrap();
    let j = v.to_json();
    assert!(j.contains("\"arr\": [1, 2, 3]"), "{}", j);
    assert!(j.contains("\"section\""), "{}", j);
}

#[test]
fn parses_float_and_bool() {
    let input = "pi = 3.14\nok = false\n";
    let v = parse(input).unwrap();
    assert!(v.to_json().contains("\"pi\": 3.14"));
    assert!(v.to_json().contains("\"ok\": false"));
}
