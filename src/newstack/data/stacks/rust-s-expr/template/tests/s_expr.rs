use {{ package_name }}::{Error, Value, eval, parse};

fn run(source: &str) -> Value {
    eval(&parse(source).expect("input should parse")).expect("input should evaluate")
}

fn failure(source: &str) -> Error {
    match parse(source) {
        Ok(value) => eval(&value).expect_err("evaluation should fail"),
        Err(error) => error,
    }
}

#[test]
fn integers_evaluate_to_themselves() {
    assert_eq!(run("42"), Value::Int(42));
    assert_eq!(run("-7"), Value::Int(-7));
}

#[test]
fn addition_is_variadic() {
    assert_eq!(run("(+ 1 2 3 4)"), Value::Int(10));
    assert_eq!(run("(+)"), Value::Int(0));
}

#[test]
fn subtraction_with_one_argument_negates() {
    assert_eq!(run("(- 5)"), Value::Int(-5));
    assert_eq!(run("(- 10 3 2)"), Value::Int(5));
}

#[test]
fn division_by_zero_is_an_error() {
    assert_eq!(failure("(/ 4 0)"), Error::Eval("division by zero".into()));
}

#[test]
fn comparisons_return_booleans() {
    assert_eq!(run("(< 1 2)"), Value::Bool(true));
    assert_eq!(run("(= 2 2)"), Value::Bool(true));
}

#[test]
fn if_evaluates_only_the_taken_branch() {
    assert_eq!(run("(if true 1 (/ 1 0))"), Value::Int(1));
    assert_eq!(run("(if false (/ 1 0) 2)"), Value::Int(2));
}

#[test]
fn and_short_circuits() {
    assert_eq!(run("(and false (/ 1 0))"), Value::Bool(false));
    assert_eq!(run("(and true true)"), Value::Bool(true));
}

#[test]
fn lists_are_first_class() {
    assert_eq!(run("(list 1 2 3)").to_string(), "(1 2 3)");
    assert_eq!(run("(car (list 1 2 3))"), Value::Int(1));
    assert_eq!(run("(cdr (list 1 2 3))").to_string(), "(2 3)");
    assert_eq!(run("(len (list 1 2 3))"), Value::Int(3));
}

#[test]
fn cons_prepends_to_a_list() {
    assert_eq!(run("(cons 0 (list 1 2))").to_string(), "(0 1 2)");
}

#[test]
fn strings_keep_escapes() {
    assert_eq!(run(r#"(str "a\tb")"#), Value::Str("a\tb".into()));
    assert_eq!(run(r#"(len "héllo")"#), Value::Int(5));
}

#[test]
fn comments_and_commas_are_whitespace() {
    assert_eq!(run("; leading\n(+ 1, 2)"), Value::Int(3));
}

#[test]
fn an_unclosed_list_is_a_parse_error() {
    match failure("(+ 1 2") {
        Error::Parse(message) => assert!(message.contains("unclosed")),
        other => panic!("expected a parse error, got {other:?}"),
    }
}

#[test]
fn an_unbound_symbol_is_an_eval_error() {
    assert_eq!(failure("nope"), Error::Eval("unbound symbol: nope".into()));
}

#[test]
fn an_unknown_function_is_reported_by_name() {
    assert_eq!(
        failure("(frobnicate 1)"),
        Error::Eval("unknown function: frobnicate".into())
    );
}

#[test]
fn trailing_input_is_rejected() {
    match failure("1 2") {
        Error::Parse(message) => assert!(message.contains("trailing input")),
        other => panic!("expected a parse error, got {other:?}"),
    }
}

#[test]
fn begin_returns_the_last_value() {
    assert_eq!(run("(begin 1 2 (list 3))").to_string(), "(3)");
}
