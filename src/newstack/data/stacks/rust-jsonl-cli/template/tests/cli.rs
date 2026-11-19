use std::fs;
use std::process::Command;

use tempfile::tempdir;

#[test]
fn select_field() {
    let dir = tempdir().unwrap();
    let p = dir.path().join("data.jsonl");
    fs::write(
        &p,
        "{\"name\":\"alice\",\"age\":30}\n{\"name\":\"bob\",\"age\":25}\n",
    )
    .unwrap();
    let bin = env!("CARGO_BIN_EXE_{{ npm_name }}");
    let output = Command::new(bin)
        .args([
            "-file",
            p.to_str().unwrap(),
            "-select",
            "name",
            "-where",
            "age==30",
        ])
        .output()
        .expect("run");
    assert!(output.status.success());
    let stdout = String::from_utf8_lossy(&output.stdout);
    assert!(stdout.contains("alice"), "{stdout}");
    assert!(!stdout.contains("bob"), "{stdout}");
}

#[test]
fn count_flag() {
    let dir = tempdir().unwrap();
    let p = dir.path().join("data.jsonl");
    fs::write(&p, "{\"a\":1}\n{\"a\":2}\n{\"a\":3}\n").unwrap();
    let bin = env!("CARGO_BIN_EXE_{{ npm_name }}");
    let output = Command::new(bin)
        .args(["-file", p.to_str().unwrap(), "-count"])
        .output()
        .expect("run");
    let stdout = String::from_utf8_lossy(&output.stdout).trim().to_string();
    assert_eq!(stdout, "3");
}
