use serde_json::Value;

pub fn eval_path(root: &Value, expr: &str) -> Result<Value, String> {
    let expr = expr.trim();
    if expr.is_empty() {
        return Err("empty expression".to_string());
    }
    // Accept optional leading '$'
    let mut rest = expr;
    let mut current = root.clone();
    if let Some(r) = rest.strip_prefix('$') {
        rest = r;
    } else if rest != "." && !rest.starts_with('[') {
        // allow bare path like "foo.bar"
    }
    if rest.is_empty() {
        return Ok(current);
    }
    while !rest.is_empty() {
        if let Some(r) = rest.strip_prefix('.') {
            rest = r;
            // read identifier
            let end = rest.find(['.', '[']).unwrap_or(rest.len());
            let key = &rest[..end];
            if key.is_empty() {
                return Err("expected key after '.'".to_string());
            }
            if let Value::Array(arr) = &current {
                let mut out = Vec::with_capacity(arr.len());
                for item in arr {
                    match item {
                        Value::Object(map) => {
                            out.push(
                                map.get(key)
                                    .cloned()
                                    .ok_or_else(|| format!("missing key: {key}"))?,
                            );
                        }
                        _ => return Err(format!("cannot index object key on non-object: {key}")),
                    }
                }
                current = Value::Array(out);
            } else if let Value::Object(map) = &current {
                current = map
                    .get(key)
                    .cloned()
                    .ok_or_else(|| format!("missing key: {key}"))?;
            } else {
                return Err(format!("cannot index object key on non-object: {key}"));
            }
            rest = &rest[end..];
        } else if let Some(r) = rest.strip_prefix('[') {
            let close = r.find(']').ok_or("missing ']'")?;
            let inner = r[..close].trim();
            let after = &r[close + 1..];
            if inner == "*" {
                match &current {
                    Value::Array(arr) => {
                        current = Value::Array(arr.clone());
                    }
                    _ => return Err("wildcard on non-array".to_string()),
                }
            } else if (inner.starts_with('"') && inner.ends_with('"'))
                || (inner.starts_with('\'') && inner.ends_with('\''))
            {
                let key = &inner[1..inner.len() - 1];
                match &current {
                    Value::Object(map) => {
                        current = map
                            .get(key)
                            .cloned()
                            .ok_or_else(|| format!("missing key: {key}"))?;
                    }
                    _ => return Err("string index on non-object".to_string()),
                }
            } else {
                let idx: i64 = inner.parse().map_err(|_| format!("bad index: {inner}"))?;
                match &current {
                    Value::Array(arr) => {
                        let i = if idx < 0 { arr.len() as i64 + idx } else { idx };
                        if i < 0 || i as usize >= arr.len() {
                            return Err(format!("index out of range: {idx}"));
                        }
                        current = arr[i as usize].clone();
                    }
                    _ => return Err("index on non-array".to_string()),
                }
            }
            rest = after;
        } else {
            return Err(format!("unexpected char in expression: {rest}"));
        }
    }
    Ok(current)
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn nested_key() {
        let v = json!({"a":{"b":1,"c":"x"},"d":true});
        assert_eq!(eval_path(&v, "$.a.b").unwrap(), json!(1));
        assert_eq!(eval_path(&v, "$.a.c").unwrap(), json!("x"));
        assert_eq!(eval_path(&v, "$.d").unwrap(), json!(true));
    }

    #[test]
    fn array_index() {
        let v = json!({"items":[10,20]});
        assert_eq!(eval_path(&v, "$.items[0]").unwrap(), json!(10));
        assert_eq!(eval_path(&v, "$.items[1]").unwrap(), json!(20));
        assert_eq!(eval_path(&v, "$.items[-1]").unwrap(), json!(20));
    }

    #[test]
    fn wildcard() {
        let v = json!({"items":[{"name":"a"},{"name":"b"}]});
        assert_eq!(eval_path(&v, "$.items[*].name").unwrap(), json!(["a", "b"]));
    }

    #[test]
    fn quoted_key() {
        let v = json!({"a-b": 5});
        assert_eq!(eval_path(&v, "$['a-b']").unwrap(), json!(5));
    }

    #[test]
    fn root() {
        let v = json!(42);
        assert_eq!(eval_path(&v, "$").unwrap(), json!(42));
    }

    #[test]
    fn missing_key_errors() {
        let v = json!({"a":1});
        assert!(eval_path(&v, "$.b").is_err());
    }
}
