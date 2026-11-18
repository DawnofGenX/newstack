use std::fs;
use std::process::Command;

use tempfile::tempdir;

#[test]
fn extracts_nested_value() {
    let dir = tempdir().unwrap();
    let path = dir.path().join("data.json");
    fs::write(&path, r#"{"a":{"b":1,"c":"x"},"d":[10,20]}"#).unwrap();
    let bin = env!("CARGO_BIN_EXE_{{ npm_name }}");
    let output = Command::new(bin)
        .arg(path.to_str().unwrap())
        .arg("$.a.b")
        .output()
        .expect("run");
    assert!(output.status.success());
    let stdout = String::from_utf8_lossy(&output.stdout).trim().to_string();
    assert_eq!(stdout, "1", "{stdout}");
}

#[test]
fn wildcard_projection() {
    let dir = tempdir().unwrap();
    let path = dir.path().join("data.json");
    fs::write(&path, r#"{"items":[{"name":"a"},{"name":"b"}]}"#).unwrap();
    let bin = env!("CARGO_BIN_EXE_{{ npm_name }}");
    let output = Command::new(bin)
        .arg(path.to_str().unwrap())
        .arg("$.items[*].name")
        .output()
        .expect("run");
    let stdout = String::from_utf8_lossy(&output.stdout).trim().to_string();
    assert_eq!(stdout, r#"["a","b"]"#, "{stdout}");
}

#[test]
fn array_index_negative() {
    let dir = tempdir().unwrap();
    let path = dir.path().join("data.json");
    fs::write(&path, r#"[5,6,7]"#).unwrap();
    let bin = env!("CARGO_BIN_EXE_{{ npm_name }}");
    let output = Command::new(bin)
        .arg(path.to_str().unwrap())
        .arg("$[-1]")
        .output()
        .expect("run");
    let stdout = String::from_utf8_lossy(&output.stdout).trim().to_string();
    assert_eq!(stdout, "7", "{stdout}");
}

#[test]
fn missing_key_fails() {
    let dir = tempdir().unwrap();
    let path = dir.path().join("data.json");
    fs::write(&path, r#"{"a":1}"#).unwrap();
    let bin = env!("CARGO_BIN_EXE_{{ npm_name }}");
    let output = Command::new(bin)
        .arg(path.to_str().unwrap())
        .arg("$.b")
        .output()
        .expect("run");
    assert!(!output.status.success());
}
