use std::process::Command;

#[test]
fn parses_hex_and_sets_bit() {
    let bin = env!("CARGO_BIN_EXE_{{ npm_name }}");
    let output = Command::new(bin)
        .args(["0", "--set", "3", "--set", "0"])
        .output()
        .expect("run");
    assert!(output.status.success());
    let stdout = String::from_utf8_lossy(&output.stdout);
    assert!(stdout.contains("9"), "{stdout}");
}

#[test]
fn clears_and_toggles() {
    let bin = env!("CARGO_BIN_EXE_{{ npm_name }}");
    let output = Command::new(bin)
        .args(["15", "--clear", "0", "--toggle", "3"])
        .output()
        .expect("run");
    assert!(output.status.success());
    let stdout = String::from_utf8_lossy(&output.stdout);
    // 15=1111, clear bit0 ->1110=14, toggle bit3 ->0110=6
    assert!(stdout.starts_with("6 "), "{stdout}");
}

#[test]
fn hex_input() {
    let bin = env!("CARGO_BIN_EXE_{{ npm_name }}");
    let output = Command::new(bin).args(["0xff"]).output().expect("run");
    assert!(output.status.success());
    let stdout = String::from_utf8_lossy(&output.stdout);
    assert!(stdout.contains("255"), "{stdout}");
}
