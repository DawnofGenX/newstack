use std::fs;
use std::process::Command;

use tempfile::tempdir;

#[test]
fn grep_finds_matches_recursively() {
    let dir = tempdir().unwrap();
    fs::create_dir_all(dir.path().join("sub")).unwrap();
    fs::write(dir.path().join("a.txt"), "Hello world\nfoo bar\n").unwrap();
    fs::write(dir.path().join("sub/b.txt"), "HELLO again\n").unwrap();

    let bin = env!("CARGO_BIN_EXE_{{ npm_name }}");
    let output = Command::new(bin)
        .arg("hello")
        .arg(dir.path())
        .arg("-i")
        .output()
        .expect("run");
    assert!(output.status.success());
    let stdout = String::from_utf8_lossy(&output.stdout);
    assert!(stdout.contains("a.txt") && stdout.contains("Hello world"));
    assert!(stdout.contains("b.txt") && stdout.contains("HELLO again"));
}

#[test]
fn line_numbers_flag() {
    let dir = tempdir().unwrap();
    fs::write(dir.path().join("f.txt"), "one\nmatch here\ntwo\n").unwrap();
    let bin = env!("CARGO_BIN_EXE_{{ npm_name }}");
    let output = Command::new(bin)
        .arg("match")
        .arg(dir.path())
        .arg("-n")
        .output()
        .expect("run");
    let stdout = String::from_utf8_lossy(&output.stdout);
    assert!(stdout.contains(":2:"), "{stdout}");
}

#[test]
fn count_flag() {
    let dir = tempdir().unwrap();
    fs::write(dir.path().join("f.txt"), "x\ny\nx\n").unwrap();
    let bin = env!("CARGO_BIN_EXE_{{ npm_name }}");
    let output = Command::new(bin)
        .arg("x")
        .arg(dir.path())
        .arg("-c")
        .output()
        .expect("run");
    let stdout = String::from_utf8_lossy(&output.stdout).trim().to_string();
    assert_eq!(stdout, "2", "{stdout}");
}
