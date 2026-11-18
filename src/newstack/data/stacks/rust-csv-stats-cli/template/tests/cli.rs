use std::process::Command;

#[test]
fn cli_runs_on_fixture() {
    let bin = env!("CARGO_BIN_EXE_{{ npm_name }}");
    let output = Command::new(bin)
        .arg("tests/fixtures/stats.csv")
        .output()
        .expect("failed to run binary");
    assert!(output.status.success(), "{:?}", output);
    let stdout = String::from_utf8_lossy(&output.stdout);
    assert!(stdout.contains("value count=3"), "{stdout}");
    assert!(stdout.contains("unique=2"), "{stdout}");
    assert!(stdout.contains("score count=3"), "{stdout}");
}
