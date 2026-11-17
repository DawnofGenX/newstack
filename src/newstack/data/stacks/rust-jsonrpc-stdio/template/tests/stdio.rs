use std::io::Write;
use std::process::{Command, Stdio};

use serde_json::Value;

/// Feed a script of request lines to the real binary and collect its answers.
fn run(input: &str) -> Vec<Value> {
    let mut child = Command::new(env!("CARGO_BIN_EXE_{{ npm_name }}"))
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .expect("the server binary should start");

    {
        let stdin = child.stdin.as_mut().expect("stdin is piped");
        stdin
            .write_all(input.as_bytes())
            .expect("write the scripted requests");
    }
    // Closing stdin is what tells the server the conversation is over; without
    // this the test hangs waiting for a process that is waiting for input.
    drop(child.stdin.take());

    let output = child.wait_with_output().expect("the server should exit");
    assert!(
        output.status.success(),
        "the server exited with {}: {}",
        output.status,
        String::from_utf8_lossy(&output.stderr)
    );

    let stdout = String::from_utf8(output.stdout).expect("stdout should be UTF-8");
    stdout
        .lines()
        .map(|line| serde_json::from_str(line).expect("every response line is JSON"))
        .collect()
}

#[test]
fn one_request_produces_exactly_one_line() {
    let responses =
        run("{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"add\",\"params\":{\"a\":2,\"b\":3}}\n");
    assert_eq!(responses.len(), 1);
    assert_eq!(responses[0]["result"]["sum"], 5);
}

#[test]
fn a_notification_does_not_occupy_a_line() {
    let responses = run(concat!(
        "{\"jsonrpc\":\"2.0\",\"method\":\"notes.put\",\"params\":{\"title\":\"t\",\"body\":\"b\"}}\n",
        "{\"jsonrpc\":\"2.0\",\"id\":2,\"method\":\"notes.list\"}\n",
    ));
    assert_eq!(
        responses.len(),
        1,
        "the notification must not produce a line"
    );
    assert_eq!(responses[0]["id"], 2);
    assert_eq!(responses[0]["result"]["count"], 1);
}

#[test]
fn state_survives_across_lines_of_the_session() {
    let responses = run(concat!(
        "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"notes.put\",\"params\":{\"title\":\"a\",\"body\":\"1\"}}\n",
        "{\"jsonrpc\":\"2.0\",\"id\":2,\"method\":\"notes.put\",\"params\":{\"title\":\"b\",\"body\":\"2\"}}\n",
        "{\"jsonrpc\":\"2.0\",\"id\":3,\"method\":\"notes.list\"}\n",
    ));
    assert_eq!(responses.len(), 3);
    assert_eq!(responses[2]["result"]["count"], 2);
}

#[test]
fn a_blank_line_and_a_bad_line_do_not_end_the_session() {
    let responses = run(concat!(
        "\n",
        "not json\n",
        "{\"jsonrpc\":\"2.0\",\"id\":9,\"method\":\"echo\",\"params\":\"still here\"}\n",
    ));
    assert_eq!(responses.len(), 2);
    assert_eq!(responses[0]["error"]["code"], -32700);
    assert_eq!(responses[1]["result"], "still here");
}

#[test]
fn the_server_exits_zero_when_stdin_closes() {
    // run() already asserts the exit status; this test names the contract.
    let responses = run("");
    assert!(responses.is_empty());
}
