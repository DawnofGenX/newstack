use serde_json::Value;

pub fn csv_to_json(input: &str) -> Result<String, String> {
    let mut rdr = csv::Reader::from_reader(input.as_bytes());
    let headers = rdr.headers().map_err(|e| e.to_string())?.clone();
    let mut rows: Vec<Value> = Vec::new();
    for result in rdr.records() {
        let record = result.map_err(|e| e.to_string())?;
        let mut obj = serde_json::Map::new();
        for (i, h) in headers.iter().enumerate() {
            let v = record.get(i).unwrap_or("");
            obj.insert(h.to_string(), Value::String(v.to_string()));
        }
        rows.push(Value::Object(obj));
    }
    serde_json::to_string(&rows).map_err(|e| e.to_string())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn basic() {
        let input = "name,age\nalice,30\nbob,25\n";
        let out = csv_to_json(input).unwrap();
        assert!(out.contains("alice"));
        assert!(out.contains("30"));
    }

    #[test]
    fn empty() {
        let out = csv_to_json("a,b\n").unwrap();
        assert_eq!(out, "[]");
    }
}
