use regex::Regex;

pub fn sed(input: &str, pattern: &str, replacement: &str, global: bool) -> Result<String, String> {
    let re = Regex::new(pattern).map_err(|e| e.to_string())?;
    let mut out = String::with_capacity(input.len());
    for line in input.split_inclusive('\n') {
        let new_line = if global {
            re.replace_all(line, replacement)
        } else {
            re.replace(line, replacement)
        };
        out.push_str(&new_line);
    }
    Ok(out)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn basic_substitute() {
        let out = sed("hello world\n", "world", "rust", false).unwrap();
        assert_eq!(out, "hello rust\n");
    }

    #[test]
    fn global_flag() {
        let out = sed("a a a\n", "a", "b", true).unwrap();
        assert_eq!(out, "b b b\n");
    }

    #[test]
    fn only_first_without_global() {
        let out = sed("a a a\n", "a", "b", false).unwrap();
        assert_eq!(out, "b a a\n");
    }

    #[test]
    fn invalid_regex() {
        assert!(sed("x", "[", "y", false).is_err());
    }
}
