//! A small s-expression reader and evaluator.
//!
//! The reader turns text into a tree, the evaluator walks the tree, and both
//! report errors as values instead of panicking so the CLI can print them and
//! exit with a failed status. Special forms (`if`, `and`, `or`) are handled
//! before their arguments are evaluated, everything else is a strict function.

use std::fmt;

/// A parsed s-expression.
#[derive(Debug, Clone, PartialEq)]
pub enum Value {
    Nil,
    Int(i64),
    Bool(bool),
    Str(String),
    Sym(String),
    List(Vec<Value>),
}

impl fmt::Display for Value {
    fn fmt(&self, out: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Value::Nil => write!(out, "nil"),
            Value::Int(value) => write!(out, "{value}"),
            Value::Bool(value) => write!(out, "{value}"),
            Value::Str(text) => write!(out, "{text}"),
            Value::Sym(text) => write!(out, "{text}"),
            Value::List(items) => {
                write!(out, "(")?;
                for (index, item) in items.iter().enumerate() {
                    if index > 0 {
                        write!(out, " ")?;
                    }
                    write!(out, "{item}")?;
                }
                write!(out, ")")
            }
        }
    }
}

/// A read or evaluation failure.
#[derive(Debug, Clone, PartialEq)]
pub enum Error {
    Parse(String),
    Eval(String),
}

impl fmt::Display for Error {
    fn fmt(&self, out: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Error::Parse(message) => write!(out, "parse: {message}"),
            Error::Eval(message) => write!(out, "eval: {message}"),
        }
    }
}

impl std::error::Error for Error {}

/// Parses one expression from `source`, ignoring `;` comments.
pub fn parse(source: &str) -> Result<Value, Error> {
    let mut reader = Reader {
        chars: source.chars().collect(),
        pos: 0,
    };
    let value = reader.value()?;
    reader.skip_space();
    if reader.pos < reader.chars.len() {
        return Err(Error::Parse(format!(
            "trailing input at character {}",
            reader.pos
        )));
    }
    Ok(value)
}

struct Reader {
    chars: Vec<char>,
    pos: usize,
}

impl Reader {
    fn peek(&self) -> Option<char> {
        self.chars.get(self.pos).copied()
    }

    fn skip_space(&mut self) {
        while let Some(current) = self.peek() {
            if current == ';' {
                while let Some(inner) = self.peek() {
                    self.pos += 1;
                    if inner == '\n' {
                        break;
                    }
                }
            } else if current.is_whitespace() || current == ',' {
                self.pos += 1;
            } else {
                break;
            }
        }
    }

    fn value(&mut self) -> Result<Value, Error> {
        self.skip_space();
        match self.peek() {
            None => Err(Error::Parse("unexpected end of input".into())),
            Some('(') => self.list(),
            Some(')') => Err(Error::Parse(format!(
                "unexpected ) at character {}",
                self.pos
            ))),
            Some('"') => self.string(),
            Some(_) => self.atom(),
        }
    }

    fn list(&mut self) -> Result<Value, Error> {
        self.pos += 1;
        let mut items = Vec::new();
        loop {
            self.skip_space();
            match self.peek() {
                None => return Err(Error::Parse("unclosed (".into())),
                Some(')') => {
                    self.pos += 1;
                    return Ok(Value::List(items));
                }
                Some(_) => items.push(self.value()?),
            }
        }
    }

    fn string(&mut self) -> Result<Value, Error> {
        self.pos += 1;
        let mut text = String::new();
        loop {
            match self.peek() {
                None => return Err(Error::Parse("unclosed string".into())),
                Some('"') => {
                    self.pos += 1;
                    return Ok(Value::Str(text));
                }
                Some('\\') => {
                    self.pos += 1;
                    match self.peek() {
                        Some('n') => text.push('\n'),
                        Some('t') => text.push('\t'),
                        Some('"') => text.push('"'),
                        Some('\\') => text.push('\\'),
                        Some(other) => return Err(Error::Parse(format!("bad escape \\{other}"))),
                        None => return Err(Error::Parse("unclosed escape".into())),
                    }
                    self.pos += 1;
                }
                Some(other) => {
                    text.push(other);
                    self.pos += 1;
                }
            }
        }
    }

    fn atom(&mut self) -> Result<Value, Error> {
        let start = self.pos;
        while let Some(current) = self.peek() {
            if current.is_whitespace() || matches!(current, '(' | ')' | ',' | ';') {
                break;
            }
            self.pos += 1;
        }
        let text: String = self.chars[start..self.pos].iter().collect();
        Ok(match text.as_str() {
            "nil" => Value::Nil,
            "true" => Value::Bool(true),
            "false" => Value::Bool(false),
            _ => match text.parse::<i64>() {
                Ok(number) => Value::Int(number),
                Err(_) => Value::Sym(text),
            },
        })
    }
}

fn int(value: &Value, context: &str) -> Result<i64, Error> {
    match value {
        Value::Int(number) => Ok(*number),
        other => Err(Error::Eval(format!(
            "{context} expects an integer, got {other}"
        ))),
    }
}

fn boolean(value: &Value, context: &str) -> Result<bool, Error> {
    match value {
        Value::Bool(flag) => Ok(*flag),
        other => Err(Error::Eval(format!(
            "{context} expects a boolean, got {other}"
        ))),
    }
}

fn list_of(value: Value, context: &str) -> Result<Vec<Value>, Error> {
    match value {
        Value::List(items) => Ok(items),
        other => Err(Error::Eval(format!(
            "{context} expects a list, got {other}"
        ))),
    }
}

/// Evaluates a parsed expression.
pub fn eval(expression: &Value) -> Result<Value, Error> {
    match expression {
        Value::List(items) => {
            let Some((head, rest)) = items.split_first() else {
                return Ok(Value::List(Vec::new()));
            };
            let Value::Sym(name) = head else {
                return Err(Error::Eval(format!("{head} is not a function")));
            };
            match name.as_str() {
                "if" => {
                    if rest.len() != 3 {
                        return Err(Error::Eval("if needs three arguments".into()));
                    }
                    if boolean(&eval(&rest[0])?, "if")? {
                        eval(&rest[1])
                    } else {
                        eval(&rest[2])
                    }
                }
                "and" => {
                    for item in rest {
                        if !boolean(&eval(item)?, "and")? {
                            return Ok(Value::Bool(false));
                        }
                    }
                    Ok(Value::Bool(true))
                }
                "or" => {
                    for item in rest {
                        if boolean(&eval(item)?, "or")? {
                            return Ok(Value::Bool(true));
                        }
                    }
                    Ok(Value::Bool(false))
                }
                "begin" => {
                    let mut last = Value::Nil;
                    for item in rest {
                        last = eval(item)?;
                    }
                    Ok(last)
                }
                _ => {
                    let mut arguments = Vec::with_capacity(rest.len());
                    for item in rest {
                        arguments.push(eval(item)?);
                    }
                    call(name, arguments)
                }
            }
        }
        Value::Sym(name) => Err(Error::Eval(format!("unbound symbol: {name}"))),
        other => Ok(other.clone()),
    }
}

fn call(name: &str, arguments: Vec<Value>) -> Result<Value, Error> {
    let described = name;
    match name {
        "+" | "*" => {
            let start = if name == "+" { 0 } else { 1 };
            let mut total = i64::from(start);
            for argument in &arguments {
                let value = int(argument, described)?;
                total = if name == "+" {
                    total.saturating_add(value)
                } else {
                    total.saturating_mul(value)
                };
            }
            Ok(Value::Int(total))
        }
        "-" | "/" | "mod" => {
            if arguments.is_empty() {
                return Err(Error::Eval(format!("{name} needs at least one argument")));
            }
            let mut values = Vec::with_capacity(arguments.len());
            for argument in &arguments {
                values.push(int(argument, described)?);
            }
            let mut result = values[0];
            if values.len() == 1 {
                return Ok(Value::Int(if name == "-" { -result } else { result }));
            }
            for value in &values[1..] {
                match name {
                    "-" => result -= value,
                    "/" => {
                        if *value == 0 {
                            return Err(Error::Eval("division by zero".into()));
                        }
                        result /= value;
                    }
                    _ => {
                        if *value == 0 {
                            return Err(Error::Eval("division by zero".into()));
                        }
                        result %= value;
                    }
                }
            }
            Ok(Value::Int(result))
        }
        "=" | "!=" | "<" | "<=" | ">" | ">=" => {
            if arguments.len() != 2 {
                return Err(Error::Eval(format!("{name} needs two arguments")));
            }
            let left = int(&arguments[0], described)?;
            let right = int(&arguments[1], described)?;
            let flag = match name {
                "=" => left == right,
                "!=" => left != right,
                "<" => left < right,
                "<=" => left <= right,
                ">" => left > right,
                _ => left >= right,
            };
            Ok(Value::Bool(flag))
        }
        "not" => {
            if arguments.len() != 1 {
                return Err(Error::Eval("not needs one argument".into()));
            }
            Ok(Value::Bool(!boolean(&arguments[0], "not")?))
        }
        "list" => Ok(Value::List(arguments)),
        "car" => {
            let items = list_of(only(arguments, "car")?, "car")?;
            Ok(items.first().cloned().unwrap_or(Value::Nil))
        }
        "cdr" => {
            let items = list_of(only(arguments, "cdr")?, "cdr")?;
            Ok(Value::List(items.into_iter().skip(1).collect()))
        }
        "cons" => {
            if arguments.len() != 2 {
                return Err(Error::Eval("cons needs two arguments".into()));
            }
            let mut items = vec![arguments[0].clone()];
            items.extend(list_of(arguments[1].clone(), "cons")?);
            Ok(Value::List(items))
        }
        "len" => match only(arguments, "len")? {
            Value::List(items) => Ok(Value::Int(items.len() as i64)),
            Value::Str(text) => Ok(Value::Int(text.chars().count() as i64)),
            other => Err(Error::Eval(format!(
                "len expects a list or string, got {other}"
            ))),
        },
        "str" => Ok(Value::Str(only(arguments, "str")?.to_string())),
        other => Err(Error::Eval(format!("unknown function: {other}"))),
    }
}

fn only(mut arguments: Vec<Value>, name: &str) -> Result<Value, Error> {
    if arguments.len() != 1 {
        return Err(Error::Eval(format!("{name} needs one argument")));
    }
    Ok(arguments.remove(0))
}
