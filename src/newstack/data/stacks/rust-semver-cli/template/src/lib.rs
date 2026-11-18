use semver::Version;

pub fn parse(input: &str) -> Result<Version, String> {
    Version::parse(input).map_err(|e| e.to_string())
}

pub fn compare(a: &str, b: &str) -> Result<i8, String> {
    let va = parse(a)?;
    let vb = parse(b)?;
    Ok(match va.cmp(&vb) {
        std::cmp::Ordering::Less => -1,
        std::cmp::Ordering::Equal => 0,
        std::cmp::Ordering::Greater => 1,
    })
}

pub fn bump(input: &str, level: &str) -> Result<String, String> {
    let mut v = parse(input)?;
    match level {
        "major" => {
            v.major += 1;
            v.minor = 0;
            v.patch = 0;
            v.pre = semver::Prerelease::EMPTY;
            v.build = semver::BuildMetadata::EMPTY;
        }
        "minor" => {
            v.minor += 1;
            v.patch = 0;
            v.pre = semver::Prerelease::EMPTY;
            v.build = semver::BuildMetadata::EMPTY;
        }
        "patch" => {
            v.patch += 1;
            v.pre = semver::Prerelease::EMPTY;
            v.build = semver::BuildMetadata::EMPTY;
        }
        _ => return Err(format!("unknown bump level: {level}")),
    }
    Ok(v.to_string())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parse_valid() {
        assert_eq!(parse("1.2.3").unwrap().to_string(), "1.2.3");
    }

    #[test]
    fn parse_rejects_garbage() {
        assert!(parse("not-a-version").is_err());
    }

    #[test]
    fn compare_table() {
        let cases = [
            ("1.0.0", "1.0.0", 0i8),
            ("1.0.0", "2.0.0", -1),
            ("2.0.0", "1.0.0", 1),
            ("1.2.3", "1.2.4", -1),
            ("1.0.0-alpha", "1.0.0", -1),
            ("1.0.0-alpha.1", "1.0.0-alpha.2", -1),
            ("1.0.0-beta", "1.0.0-alpha", 1),
        ];
        for (a, b, expected) in cases {
            assert_eq!(compare(a, b).unwrap(), expected, "{a} vs {b}");
        }
    }

    #[test]
    fn bump_table() {
        let cases = [
            ("1.2.3", "major", "2.0.0"),
            ("1.2.3", "minor", "1.3.0"),
            ("1.2.3", "patch", "1.2.4"),
            ("1.0.0-rc.1", "patch", "1.0.1"),
        ];
        for (v, level, expected) in cases {
            assert_eq!(bump(v, level).unwrap(), expected, "{v} {level}");
        }
    }

    #[test]
    fn bump_rejects_bad_level() {
        assert!(bump("1.0.0", "foo").is_err());
    }
}
