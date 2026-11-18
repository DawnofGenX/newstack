use std::process::Command;

#[test]
fn parse_prints_version() {
    let bin = env!("CARGO_BIN_EXE_{{ npm_name }}");
    let output = Command::new(bin)
        .args(["parse", "1.2.3-rc.1"])
        .output()
        .expect("run");
    assert!(output.status.success());
    assert_eq!(String::from_utf8_lossy(&output.stdout).trim(), "1.2.3-rc.1");
}

#[test]
fn compare_prerelease_ordering() {
    let bin = env!("CARGO_BIN_EXE_{{ npm_name }}");
    let output = Command::new(bin)
        .args(["compare", "1.0.0-alpha", "1.0.0"])
        .output()
        .expect("run");
    assert_eq!(String::from_utf8_lossy(&output.stdout).trim(), "-1");
}

#[test]
fn bump_major() {
    let bin = env!("CARGO_BIN_EXE_{{ npm_name }}");
    let output = Command::new(bin)
        .args(["bump", "1.2.3", "major"])
        .output()
        .expect("run");
    assert_eq!(String::from_utf8_lossy(&output.stdout).trim(), "2.0.0");
}

#[test]
fn bump_rejects_bad() {
    let bin = env!("CARGO_BIN_EXE_{{ npm_name }}");
    let output = Command::new(bin)
        .args(["bump", "1.2.3", "nope"])
        .output()
        .expect("run");
    assert!(!output.status.success());
}
