use std::fs;
use std::process::Command;

use tempfile::tempdir;

#[test]
fn dumps_file() {
    let dir = tempdir().unwrap();
    let path = dir.path().join("data.bin");
    fs::write(&path, b"abc").unwrap();
    let bin = env!("CARGO_BIN_EXE_{{ npm_name }}");
    let output = Command::new(bin)
        .arg(path.to_str().unwrap())
        .output()
        .expect("run");
    assert!(output.status.success());
    let stdout = String::from_utf8_lossy(&output.stdout);
    assert!(stdout.contains("61 62 63"));
    assert!(stdout.contains("abc"));
}

#[test]
fn reads_stdin() {
    let bin = env!("CARGO_BIN_EXE_{{ npm_name }}");
    let mut child = Command::new(bin)
        .stdin(std::process::Stdio::piped())
        .stdout(std::process::Stdio::piped())
        .spawn()
        .expect("spawn");
    use std::io::Write;
    child.stdin.as_mut().unwrap().write_all(b"Hi").unwrap();
    let out = child.wait_with_output().expect("wait");
    let stdout = String::from_utf8_lossy(&out.stdout);
    assert!(stdout.contains("48 69"));
}

#[test]
fn missing_file_fails() {
    let bin = env!("CARGO_BIN_EXE_{{ npm_name }}");
    let output = Command::new(bin)
        .arg("/no/such/file.bin")
        .output()
        .expect("run");
    assert!(!output.status.success());
}
