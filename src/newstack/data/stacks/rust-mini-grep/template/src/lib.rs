use std::fs::File;
use std::io::{BufRead, BufReader};
use std::path::Path;

use regex::RegexBuilder;
use walkdir::WalkDir;

#[derive(Debug, Clone)]
pub struct Match {
    pub path: String,
    pub line_number: usize,
    pub line: String,
}

#[derive(Debug, Clone, Copy)]
pub struct Options {
    pub ignore_case: bool,
    pub line_number: bool,
    pub count_only: bool,
}

pub fn search_dir(root: &Path, pattern: &str, options: Options) -> Result<Vec<Match>, String> {
    let regex = RegexBuilder::new(pattern)
        .case_insensitive(options.ignore_case)
        .build()
        .map_err(|e| e.to_string())?;

    let mut matches = Vec::new();
    for entry in WalkDir::new(root).into_iter().filter_map(|e| e.ok()) {
        let path = entry.path();
        if !path.is_file() {
            continue;
        }
        let Ok(file) = File::open(path) else {
            continue;
        };
        let reader = BufReader::new(file);
        for (idx, line) in reader.lines().enumerate() {
            let Ok(line) = line else {
                break;
            };
            if regex.is_match(&line) {
                matches.push(Match {
                    path: path.display().to_string(),
                    line_number: idx + 1,
                    line,
                });
            }
        }
    }
    Ok(matches)
}

pub fn count_matches(matches: &[Match]) -> usize {
    matches.len()
}
