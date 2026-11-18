use std::collections::BTreeSet;
use std::fs::File;
use std::path::Path;

use csv::Reader;
use serde::Serialize;

#[derive(Debug, Clone, Serialize)]
pub struct ColumnStats {
    pub name: String,
    pub count: usize,
    pub min: Option<f64>,
    pub max: Option<f64>,
    pub mean: Option<f64>,
    pub unique: usize,
}

struct Accumulator {
    count: usize,
    sum: f64,
    min: Option<f64>,
    max: Option<f64>,
    all_numeric: bool,
    seen: BTreeSet<String>,
}

impl Accumulator {
    fn new() -> Self {
        Self {
            count: 0,
            sum: 0.0,
            min: None,
            max: None,
            all_numeric: true,
            seen: BTreeSet::new(),
        }
    }

    fn push(&mut self, value: &str) {
        self.count += 1;
        self.seen.insert(value.to_owned());
        match value.parse::<f64>() {
            Ok(number) => {
                self.sum += number;
                self.min = Some(self.min.map_or(number, |current| current.min(number)));
                self.max = Some(self.max.map_or(number, |current| current.max(number)));
            }
            Err(_) => {
                self.all_numeric = false;
            }
        }
    }

    fn finish(self, name: String) -> ColumnStats {
        let (min, max, mean) = if self.all_numeric && self.count > 0 {
            (self.min, self.max, Some(self.sum / self.count as f64))
        } else {
            (None, None, None)
        };
        ColumnStats {
            name,
            count: self.count,
            min,
            max,
            mean,
            unique: self.seen.len(),
        }
    }
}

pub fn analyze_reader<R: std::io::Read>(reader: R) -> Result<Vec<ColumnStats>, csv::Error> {
    let mut reader = Reader::from_reader(reader);
    let headers = reader.headers()?.clone();
    let mut accumulators: Vec<Accumulator> =
        (0..headers.len()).map(|_| Accumulator::new()).collect();

    for result in reader.records() {
        let record = result?;
        for (index, field) in record.iter().enumerate() {
            if let Some(accumulator) = accumulators.get_mut(index) {
                accumulator.push(field);
            }
        }
    }

    Ok(headers
        .iter()
        .enumerate()
        .map(|(index, name)| {
            let accumulator = accumulators
                .get_mut(index)
                .map(std::mem::take)
                .unwrap_or_else(Accumulator::new);
            accumulator.finish(name.to_owned())
        })
        .collect())
}

pub fn analyze_path(path: &Path) -> Result<Vec<ColumnStats>, Box<dyn std::error::Error>> {
    let file = File::open(path)?;
    Ok(analyze_reader(file)?)
}

impl Default for Accumulator {
    fn default() -> Self {
        Self::new()
    }
}
