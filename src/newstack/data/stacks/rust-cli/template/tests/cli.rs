//! End-to-end tests over the public API: parse the arguments a user would
//! type, then run the resulting command through `greet`.

use {{ package_name }}::{Command, DEFAULT_NAME, VERSION, greet, parse};

fn run(args: &[&str]) -> Result<Command, String> {
    parse(args.iter().map(|arg| arg.to_string()))
}

fn greet_for(args: &[&str]) -> String {
    match run(args).expect("arguments should parse") {
        Command::Greet(name) => greet(&name),
        other => panic!("expected a greet command, got {other:?}"),
    }
}

#[test]
fn bare_invocation_greets_the_default_name() {
    assert_eq!(greet_for(&[]), format!("Hello, {DEFAULT_NAME}!"));
}

#[test]
fn greet_subcommand_with_name() {
    assert_eq!(greet_for(&["greet", "--name", "you"]), "Hello, you!");
}

#[test]
fn equals_form_matches_space_form() {
    assert_eq!(
        greet_for(&["--name=you"]),
        greet_for(&["greet", "--name", "you"])
    );
}

#[test]
fn version_reports_cargo_version() {
    assert_eq!(run(&["--version"]), Ok(Command::Version));
    assert_eq!(VERSION, env!("CARGO_PKG_VERSION"));
}

#[test]
fn unknown_flag_reports_usage() {
    let message = run(&["--nope"]).expect_err("unknown flags must fail");
    assert!(message.contains("--nope"));
    assert!(message.contains("usage:"));
}
