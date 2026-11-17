use {{ package_name }}::{Dispatcher, INVALID_PARAMS, INVALID_REQUEST, METHOD_NOT_FOUND, PARSE_ERROR};
use serde_json::{Value, json};

fn ask(dispatcher: &mut Dispatcher, line: &str) -> Value {
    dispatcher
        .handle_line(line)
        .unwrap_or_else(|| panic!("expected a response for {line}"))
}

fn error_code(response: &Value) -> i64 {
    response["error"]["code"]
        .as_i64()
        .unwrap_or_else(|| panic!("no error code in {response}"))
}

#[test]
fn add_returns_the_sum() {
    let mut dispatcher = Dispatcher::new();
    let response = ask(
        &mut dispatcher,
        r#"{"jsonrpc":"2.0","id":1,"method":"add","params":{"a":2,"b":3}}"#,
    );
    assert_eq!(response, json!({"jsonrpc":"2.0","id":1,"result":{"sum":5}}));
}

#[test]
fn echo_returns_the_params_untouched() {
    let mut dispatcher = Dispatcher::new();
    let response = ask(
        &mut dispatcher,
        r#"{"jsonrpc":"2.0","id":"abc","method":"echo","params":{"nested":[1,2]}}"#,
    );
    assert_eq!(
        response["id"],
        json!("abc"),
        "a string id must come back as a string"
    );
    assert_eq!(response["result"], json!({"nested":[1,2]}));
}

#[test]
fn notes_round_trip_through_the_dispatcher() {
    let mut dispatcher = Dispatcher::new();
    let stored = ask(
        &mut dispatcher,
        r#"{"jsonrpc":"2.0","id":1,"method":"notes.put","params":{"title":"a","body":"first"}}"#,
    );
    assert_eq!(stored["result"], json!({"stored":1}));

    ask(
        &mut dispatcher,
        r#"{"jsonrpc":"2.0","id":2,"method":"notes.put","params":{"title":"b","body":"second"}}"#,
    );
    let listed = ask(
        &mut dispatcher,
        r#"{"jsonrpc":"2.0","id":3,"method":"notes.list"}"#,
    );
    assert_eq!(listed["result"]["count"], json!(2));
    assert_eq!(listed["result"]["notes"][0]["title"], json!("a"));

    let dropped = ask(
        &mut dispatcher,
        r#"{"jsonrpc":"2.0","id":4,"method":"notes.drop","params":{"title":"a"}}"#,
    );
    assert_eq!(dropped["result"], json!({"removed":true}));

    let again = ask(
        &mut dispatcher,
        r#"{"jsonrpc":"2.0","id":5,"method":"notes.drop","params":{"title":"a"}}"#,
    );
    assert_eq!(
        again["result"],
        json!({"removed":false}),
        "dropping twice is not an error"
    );
}

#[test]
fn a_notification_is_executed_but_never_answered() {
    let mut dispatcher = Dispatcher::new();
    let response = dispatcher
        .handle_line(r#"{"jsonrpc":"2.0","method":"notes.put","params":{"title":"t","body":"b"}}"#);
    assert!(
        response.is_none(),
        "a request without an id must produce no response"
    );
    assert_eq!(dispatcher.handled(), 1, "but it must still run");

    let listed = ask(
        &mut dispatcher,
        r#"{"jsonrpc":"2.0","id":1,"method":"notes.list"}"#,
    );
    assert_eq!(listed["result"]["count"], json!(1));
}

#[test]
fn an_unknown_method_is_method_not_found() {
    let mut dispatcher = Dispatcher::new();
    let response = ask(
        &mut dispatcher,
        r#"{"jsonrpc":"2.0","id":7,"method":"nope"}"#,
    );
    assert_eq!(error_code(&response), METHOD_NOT_FOUND);
    assert_eq!(response["id"], json!(7));
}

#[test]
fn bad_params_carry_the_offending_value_as_data() {
    let mut dispatcher = Dispatcher::new();
    let response = ask(
        &mut dispatcher,
        r#"{"jsonrpc":"2.0","id":1,"method":"add","params":{"a":"two","b":3}}"#,
    );
    assert_eq!(error_code(&response), INVALID_PARAMS);
    assert_eq!(response["error"]["data"], json!({"a":"two","b":3}));
}

#[test]
fn a_malformed_line_is_a_parse_error_with_a_null_id() {
    let mut dispatcher = Dispatcher::new();
    let response = ask(&mut dispatcher, "{not json");
    assert_eq!(error_code(&response), PARSE_ERROR);
    assert_eq!(response["id"], Value::Null);
}

#[test]
fn a_request_without_a_method_is_an_invalid_request() {
    let mut dispatcher = Dispatcher::new();
    let response = ask(&mut dispatcher, r#"{"jsonrpc":"2.0","id":1}"#);
    assert_eq!(error_code(&response), INVALID_REQUEST);
}

#[test]
fn the_wrong_protocol_version_is_an_invalid_request() {
    let mut dispatcher = Dispatcher::new();
    let response = ask(
        &mut dispatcher,
        r#"{"jsonrpc":"1.0","id":1,"method":"echo"}"#,
    );
    assert_eq!(error_code(&response), INVALID_REQUEST);
}

#[test]
fn a_batch_comes_back_as_one_array_in_order() {
    let mut dispatcher = Dispatcher::new();
    let response = ask(
        &mut dispatcher,
        r#"[{"jsonrpc":"2.0","id":1,"method":"add","params":{"a":1,"b":1}},{"jsonrpc":"2.0","id":2,"method":"add","params":{"a":2,"b":2}}]"#,
    );
    let array = response.as_array().expect("a batch answers with an array");
    assert_eq!(array.len(), 2);
    assert_eq!(array[0]["result"]["sum"], json!(2));
    assert_eq!(array[1]["result"]["sum"], json!(4));
}

#[test]
fn a_batch_of_only_notifications_gets_no_answer() {
    let mut dispatcher = Dispatcher::new();
    let response = dispatcher.handle_line(
        r#"[{"jsonrpc":"2.0","method":"echo","params":1},{"jsonrpc":"2.0","method":"echo","params":2}]"#,
    );
    assert!(response.is_none(), "nothing to answer means no line at all");
}

#[test]
fn an_empty_batch_is_one_invalid_request_not_an_empty_array() {
    let mut dispatcher = Dispatcher::new();
    let response = ask(&mut dispatcher, "[]");
    assert_eq!(error_code(&response), INVALID_REQUEST);
}

#[test]
fn blank_lines_are_ignored() {
    let mut dispatcher = Dispatcher::new();
    assert!(dispatcher.handle_line("").is_none());
    assert!(dispatcher.handle_line("   ").is_none());
    assert_eq!(dispatcher.handled(), 0);
}
