use std::io::BufRead;

/// Extract a top-level string/number field value from a JSON object line.
pub fn get_field(line: &str, field: &str) -> Option<String> {
    let key = format!("\"{}\"", field);
    let idx = line.find(&key)?;
    let rest = &line[idx + key.len()..];
    // skip colon and whitespace
    let rest = rest.trim_start();
    let rest = rest.strip_prefix(':')?;
    let rest = rest.trim_start();
    if let Some(inner) = rest.strip_prefix('"') {
        let end = inner.find('"')?;
        Some(inner[..end].to_string())
    } else {
        // number or bool/null
        let end = rest
            .find(|c: char| c == ',' || c == '}' || c.is_whitespace())
            .unwrap_or(rest.len());
        Some(rest[..end].to_string())
    }
}

#[derive(Debug, Clone)]
pub struct Record {
    pub line: String,
}

pub fn query_jsonl<R: BufRead>(
    reader: R,
    select: Option<&str>,
    where_field: Option<&str>,
    where_value: Option<&str>,
    count_only: bool,
) -> (Vec<String>, usize) {
    let mut out = Vec::new();
    let mut total = 0usize;
    for line in reader.lines() {
        let Ok(line) = line else { continue };
        let line = line.trim().to_string();
        if line.is_empty() {
            continue;
        }
        // filter
        if let (Some(f), Some(v)) = (where_field, where_value) {
            match get_field(&line, f) {
                Some(val) if val == *v => {}
                _ => continue,
            }
        }
        total += 1;
        if count_only {
            continue;
        }
        match select {
            Some(f) => {
                if let Some(val) = get_field(&line, f) {
                    out.push(val);
                } else {
                    out.push(String::new());
                }
            }
            None => out.push(line),
        }
    }
    (out, total)
}

pub fn count_matches(n: usize) -> usize {
    n
}
