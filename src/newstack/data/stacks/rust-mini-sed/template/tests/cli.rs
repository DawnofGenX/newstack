use std::fs;
use std::io::Write;
use std::process::Command;

use tempfile::tempdir;

#[test]
fn substitutes_stdin() {
    let bin = env!("CARGO_BIN_EXE_{{ npm_name }}");
    let mut child = Command::new(bin)
        .args(["world", "rust"])
        .stdin(std::process::Stdio::piped())
        .stdout(std::process::Stdio::piped())
        .spawn()
        .expect("spawn");
    child
        .stdin
        .as_mut()
        .unwrap()
        .write_all(b"hello world\n")
        .unwrap();
    let out = child.wait_with_output().expect("wait");
    assert!(out.status.success());
    let stdout = String::from_utf8_lossy(&out.stdout);
    assert!(stdout.contains("hello rust"));
}

#[test]
fn global_flag() {
    let tmp = tempdir().unwrap();
    let f = tmp.path().join("in.txt");
    fs::write(&f, "a a a\n").unwrap();
    let bin = env!("CARGO_BIN_EXE_{{ npm_name }}");
    let output = Command::new(bin)
        .args(["a", "b", "-g"])
        .arg(&f)
        .output()
        .expect("run");
    assert!(output.status.success());
    let stdout = String::from_utf8_lossy(&output.stdout);
    assert!(stdout.contains("b b b"));
}

#[test]
fn file_input() {
    let tmp = tempdir().unwrap();
    let f = tmp.path().join("in.txt");
    fs::write(&f, "foo bar\n").unwrap();
    let bin = env!("CARGO_BIN_EXE_{{ npm_name }}");
    let output = Command::new(bin)
        .args(["foo", "baz"])
        .arg(&f)
        .output()
        .expect("run");
    assert!(output.status.success());
    let stdout = String::from_utf8_lossy(&output.stdout);
    assert!(stdout.contains("baz bar"));
}
