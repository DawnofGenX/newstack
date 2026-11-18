use std::collections::BTreeMap;

#[derive(Debug, Clone, PartialEq)]
pub enum Value {
    Bool(bool),
    Int(i64),
    Float(f64),
    Str(String),
    Array(Vec<Value>),
    Table(BTreeMap<String, Value>),
}

impl Value {
    pub fn table() -> Self {
        Value::Table(BTreeMap::new())
    }

    pub fn get(&self, key: &str) -> Option<&Value> {
        match self {
            Value::Table(t) => t.get(key),
            _ => None,
        }
    }

    pub fn to_json(&self) -> String {
        match self {
            Value::Bool(b) => {
                if *b {
                    "true".to_string()
                } else {
                    "false".to_string()
                }
            }
            Value::Int(i) => i.to_string(),
            Value::Float(f) => {
                let s = format!("{}", f);
                if s.contains('.') || s.contains('e') || s.contains('E') {
                    s
                } else {
                    format!("{}.0", s)
                }
            }
            Value::Str(s) => format!("\"{}\"", escape(s)),
            Value::Array(a) => {
                let parts: Vec<String> = a.iter().map(|v| v.to_json()).collect();
                format!("[{}]", parts.join(", "))
            }
            Value::Table(t) => {
                let parts: Vec<String> = t
                    .iter()
                    .map(|(k, v)| format!("\"{}\": {}", escape(k), v.to_json()))
                    .collect();
                format!("{{{}}}", parts.join(", "))
            }
        }
    }
}

fn escape(s: &str) -> String {
    let mut out = String::new();
    for c in s.chars() {
        match c {
            '"' => out.push_str("\\\""),
            '\\' => out.push_str("\\\\"),
            '\n' => out.push_str("\\n"),
            '\r' => out.push_str("\\r"),
            '\t' => out.push_str("\\t"),
            c if (c as u32) < 0x20 => out.push_str(&format!("\\u{:04x}", c as u32)),
            c => out.push(c),
        }
    }
    out
}

fn split_top_commas(s: &str) -> Vec<String> {
    let mut parts = Vec::new();
    let mut depth = 0i32;
    let mut in_str = false;
    let mut cur = String::new();
    let mut chars = s.chars().peekable();
    while let Some(c) = chars.next() {
        if in_str {
            cur.push(c);
            if c == '\\' {
                if let Some(n) = chars.next() {
                    cur.push(n);
                }
            } else if c == '"' {
                in_str = false;
            }
        } else {
            match c {
                '"' => {
                    in_str = true;
                    cur.push(c);
                }
                '[' => {
                    depth += 1;
                    cur.push(c);
                }
                ']' => {
                    depth -= 1;
                    cur.push(c);
                }
                ',' if depth == 0 => {
                    parts.push(cur.clone());
                    cur.clear();
                }
                _ => cur.push(c),
            }
        }
    }
    if !cur.trim().is_empty() {
        parts.push(cur);
    }
    parts
}

fn parse_string(s: &str) -> Result<String, String> {
    // s starts and ends with quote
    let inner = &s[1..s.len() - 1];
    let mut out = String::new();
    let mut chars = inner.chars();
    while let Some(c) = chars.next() {
        if c == '\\' {
            match chars.next() {
                Some('n') => out.push('\n'),
                Some('t') => out.push('\t'),
                Some('r') => out.push('\r'),
                Some('"') => out.push('"'),
                Some('\\') => out.push('\\'),
                Some(other) => {
                    out.push('\\');
                    out.push(other);
                }
                None => return Err("bad escape".to_string()),
            }
        } else {
            out.push(c);
        }
    }
    Ok(out)
}

pub fn parse_value(s: &str) -> Result<Value, String> {
    let s = s.trim();
    if s.is_empty() {
        return Err("empty value".to_string());
    }
    if s.starts_with('"') && s.ends_with('"') && s.len() >= 2 {
        return Ok(Value::Str(parse_string(s)?));
    }
    if s.starts_with('[') && s.ends_with(']') {
        let inner = s[1..s.len() - 1].trim();
        if inner.is_empty() {
            return Ok(Value::Array(vec![]));
        }
        let parts = split_top_commas(inner);
        let mut arr = Vec::new();
        for p in parts {
            arr.push(parse_value(p.trim())?);
        }
        return Ok(Value::Array(arr));
    }
    if s == "true" {
        return Ok(Value::Bool(true));
    }
    if s == "false" {
        return Ok(Value::Bool(false));
    }
    if let Ok(i) = s.parse::<i64>() {
        return Ok(Value::Int(i));
    }
    if let Ok(f) = s.parse::<f64>() {
        return Ok(Value::Float(f));
    }
    Err(format!("invalid value: {}", s))
}

#[allow(clippy::collapsible_if, clippy::single_match)]
fn ensure_table(root: &mut Value, path: &[String]) {
    let mut cur = root;
    for seg in path {
        if let Value::Table(t) = cur {
            if !t.contains_key(seg) {
                t.insert(seg.clone(), Value::Table(BTreeMap::new()));
            }
        }
        if let Value::Table(t) = cur {
            cur = t.get_mut(seg).unwrap();
        } else {
            break;
        }
    }
}

fn insert(root: &mut Value, path: &[String], key: &str, val: Value) {
    // navigate to table at path, creating
    let mut cur = root;
    for seg in path {
        if let Value::Table(t) = cur {
            if !t.contains_key(seg) {
                t.insert(seg.clone(), Value::Table(BTreeMap::new()));
            }
            cur = t.get_mut(seg).unwrap();
        } else {
            return;
        }
    }
    if let Value::Table(t) = cur {
        t.insert(key.to_string(), val);
    }
}

pub fn parse(input: &str) -> Result<Value, String> {
    let mut root = Value::Table(BTreeMap::new());
    let mut current: Vec<String> = Vec::new();
    for raw in input.lines() {
        let line = raw.trim();
        if line.is_empty() || line.starts_with('#') {
            continue;
        }
        if line.starts_with('[') && line.ends_with(']') {
            let name = line[1..line.len() - 1].trim();
            current = name.split('.').map(|s| s.trim().to_string()).collect();
            ensure_table(&mut root, &current);
        } else {
            let eq = match line.find('=') {
                Some(i) => i,
                None => return Err(format!("expected '=' in: {}", line)),
            };
            let key = line[..eq].trim().to_string();
            let valstr = line[eq + 1..].trim();
            let v = parse_value(valstr)?;
            insert(&mut root, &current, &key, v);
        }
    }
    Ok(root)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn basic() {
        let input = "title = \"hi\"\nn = 42\npi = 3.14\nflag = true\narr = [1, 2, 3]\n\n[section]\nx = 1\n";
        let v = parse(input).unwrap();
        assert_eq!(v.get("title"), Some(&Value::Str("hi".to_string())));
        let t = v.get("section").unwrap();
        assert_eq!(t.get("x"), Some(&Value::Int(1)));
        let arr = v.get("arr").unwrap();
        assert_eq!(arr, &Value::Array(vec![Value::Int(1), Value::Int(2), Value::Int(3)]));
    }

    #[test]
    fn nested_table() {
        let input = "[a.b]\nx = 5\n";
        let v = parse(input).unwrap();
        let a = v.get("a").unwrap();
        let b = a.get("b").unwrap();
        assert_eq!(b.get("x"), Some(&Value::Int(5)));
    }
}
