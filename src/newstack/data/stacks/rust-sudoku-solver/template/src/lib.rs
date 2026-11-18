//! A small Sudoku solver: parsing, validation and backtracking with bit masks.

use std::fmt;

/// Side of the board.
pub const SIZE: usize = 9;
/// Number of cells on the board.
pub const CELLS: usize = SIZE * SIZE;

/// A problem with the puzzle text.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ParseError {
    message: String,
}

impl ParseError {
    fn new(message: impl Into<String>) -> Self {
        Self {
            message: message.into(),
        }
    }
}

impl fmt::Display for ParseError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.message)
    }
}

impl std::error::Error for ParseError {}

fn row_of(index: usize) -> usize {
    index / SIZE
}

fn col_of(index: usize) -> usize {
    index % SIZE
}

fn box_of(index: usize) -> usize {
    (row_of(index) / 3) * 3 + col_of(index) / 3
}

/// Reads a puzzle, where `0` and `.` both mean empty and whitespace is ignored.
pub fn parse(text: &str) -> Result<Vec<u8>, ParseError> {
    let mut grid = Vec::with_capacity(CELLS);
    for (offset, ch) in text.chars().filter(|c| !c.is_whitespace()).enumerate() {
        let value = match ch {
            '.' => 0,
            '1'..='9' => ch as u8 - b'0',
            '0' => 0,
            _ => {
                return Err(ParseError::new(format!(
                    "invalid character {ch:?} at position {}",
                    offset + 1
                )));
            }
        };
        grid.push(value);
    }
    if grid.len() != CELLS {
        return Err(ParseError::new(format!(
            "expected {CELLS} cells, got {}",
            grid.len()
        )));
    }
    Ok(grid)
}

/// Renders the board with dots for empty cells.
pub fn format(grid: &[u8]) -> String {
    let mut out = String::with_capacity(CELLS * 2 + SIZE);
    for row in 0..SIZE {
        if row > 0 {
            out.push('\n');
        }
        for col in 0..SIZE {
            if col > 0 {
                out.push(' ');
            }
            let value = grid[row * SIZE + col];
            if value == 0 {
                out.push('.');
            } else {
                out.push((b'0' + value) as char);
            }
        }
    }
    out
}

/// Returns the digits that may legally go into an empty cell.
pub fn candidates(grid: &[u8], index: usize) -> Vec<u8> {
    if index >= CELLS || grid[index] != 0 {
        return Vec::new();
    }
    let mut used = 0u16;
    let (row, col, block) = (row_of(index), col_of(index), box_of(index));
    for (other, value) in grid.iter().enumerate() {
        if other == index || *value == 0 {
            continue;
        }
        if row_of(other) == row || col_of(other) == col || box_of(other) == block {
            used |= 1 << *value;
        }
    }
    (1..=9u8).filter(|digit| used & (1 << digit) == 0).collect()
}

/// True when no row, column or box repeats a digit.
pub fn is_valid(grid: &[u8]) -> bool {
    if grid.len() != CELLS {
        return false;
    }
    if grid.iter().any(|value| *value > 9) {
        return false;
    }
    let mut rows = [0u16; SIZE];
    let mut cols = [0u16; SIZE];
    let mut blocks = [0u16; SIZE];
    for (index, value) in grid.iter().enumerate() {
        if *value == 0 {
            continue;
        }
        let bit = 1u16 << value;
        let (row, col, block) = (row_of(index), col_of(index), box_of(index));
        if rows[row] & bit != 0 || cols[col] & bit != 0 || blocks[block] & bit != 0 {
            return false;
        }
        rows[row] |= bit;
        cols[col] |= bit;
        blocks[block] |= bit;
    }
    true
}

/// True when every cell holds a digit and the grid is valid.
pub fn is_complete(grid: &[u8]) -> bool {
    grid.len() == CELLS && grid.iter().all(|value| *value != 0) && is_valid(grid)
}

fn best_cell(grid: &[u8]) -> Option<(usize, Vec<u8>)> {
    let mut best: Option<(usize, Vec<u8>)> = None;
    for index in 0..CELLS {
        if grid[index] != 0 {
            continue;
        }
        let options = candidates(grid, index);
        if options.is_empty() {
            return None;
        }
        let count = options.len();
        let better = match &best {
            Some((_, current)) => count < current.len(),
            None => true,
        };
        if better {
            best = Some((index, options));
            if count == 1 {
                break;
            }
        }
    }
    best
}

/// Solves the puzzle, returning `None` when it has no solution.
pub fn solve(grid: &[u8]) -> Option<Vec<u8>> {
    if grid.len() != CELLS || !is_valid(grid) {
        return None;
    }
    let mut work = grid.to_vec();
    search(&mut work).then_some(work)
}

fn search(grid: &mut [u8]) -> bool {
    let Some((index, options)) = best_cell(grid) else {
        return is_complete(grid);
    };
    for option in options {
        grid[index] = option;
        if search(grid) {
            return true;
        }
        grid[index] = 0;
    }
    false
}

/// Counts solutions, stopping at `limit` so ambiguous puzzles stay cheap.
pub fn count_solutions(grid: &[u8], limit: usize) -> usize {
    if grid.len() != CELLS || !is_valid(grid) {
        return 0;
    }
    fn count(grid: &mut [u8], limit: usize) -> usize {
        let Some((index, options)) = best_cell(grid) else {
            return usize::from(is_complete(grid));
        };
        let mut total = 0;
        for option in options {
            grid[index] = option;
            total += count(grid, limit);
            grid[index] = 0;
            if total >= limit {
                break;
            }
        }
        total
    }
    count(&mut grid.to_vec(), limit.max(1))
}
