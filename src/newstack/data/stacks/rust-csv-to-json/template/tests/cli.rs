use std::fs;
use std::process::Command;

use tempfile::tempdir;

#[test]
fn converts_csv_file() {
    let dir = tempdir().unwrap();
    let csv = dir.path().join("in.csv");
    fs::write(&csv, "name,age\nalice,30\nbob,25\n").unwrap();
    let bin = env!("CARGO_BIN_EXE_{{ npm_name }}");
    let output = Command::new(bin).arg(&csv).output().expect("run");
    assert!(output.status.success());
    let stdout = String::from_utf8_lossy(&output.stdout);
    assert!(stdout.contains("alice") && stdout.contains("30"));
    assert!(stdout.contains("bob") && stdout.contains("25"));
}

#[test]
fn reads_stdin() {
    use std::io::Write;
    let bin = env!("CARGO_BIN_EXE_{{ npm_name }}");
    let mut child = Command::new(bin)
        .stdin(std::process::Stdio::piped())
        .stdout(std::process::Stdio::piped())
        .spawn()
        .expect("spawn");
    child
        .stdin
        .as_mut()
        .unwrap()
        .write_all(b"a,b\n1,2\n")
        .unwrap();
    let output = child.wait_with_output().expect("wait");
    assert!(output.status.success());
    let stdout = String::from_utf8_lossy(&output.stdout);
    assert!(stdout.contains("\"a\":\"1\""));
}
