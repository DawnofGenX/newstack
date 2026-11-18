use {{ package_name }}::{candidates, count_solutions, format, is_complete, is_valid, parse, solve};

const PUZZLE: &str =
    "530070000600195000098000060800060003400803001700020006060000280000419005000080079";
const SOLUTION: &str =
    "534678912672195348198342567859761423426853791713924856961537284287419635345286179";

#[test]
fn parses_digits_and_dots() {
    let grid = parse(PUZZLE).expect("puzzle should parse");
    assert_eq!(grid.len(), 81);
    assert_eq!(grid[0], 5);
    assert_eq!(grid[2], 0);
    let spaced = parse(&PUZZLE[..9]).is_err();
    assert!(spaced, "a short puzzle must be rejected");
}

#[test]
fn parse_ignores_whitespace() {
    let pretty = format(&parse(PUZZLE).unwrap());
    let grid = parse(&pretty.replace(' ', "\n")).expect("pretty board should parse");
    assert_eq!(grid, parse(PUZZLE).unwrap());
}

#[test]
fn parse_reports_bad_characters() {
    let mut text = PUZZLE.to_string();
    text.replace_range(0..1, "x");
    let error = parse(&text).unwrap_err().to_string();
    assert!(error.contains("invalid character"), "got {error}");
}

#[test]
fn parse_reports_the_cell_count() {
    let error = parse("123").unwrap_err().to_string();
    assert!(error.contains("expected 81 cells, got 3"), "got {error}");
}

#[test]
fn solves_a_known_puzzle() {
    let grid = parse(PUZZLE).unwrap();
    let solution = solve(&grid).expect("puzzle is solvable");
    assert_eq!(format(&solution).replace(['\n', ' '], ""), SOLUTION);
    assert!(is_complete(&solution));
}

#[test]
fn a_unique_puzzle_has_one_solution() {
    let grid = parse(PUZZLE).unwrap();
    assert_eq!(count_solutions(&grid, 2), 1);
}

#[test]
fn an_empty_board_has_many_solutions() {
    let grid = vec![0u8; 81];
    assert_eq!(count_solutions(&grid, 2), 2);
}

#[test]
fn contradictory_puzzles_are_unsolvable() {
    let mut grid = parse(PUZZLE).unwrap();
    grid[1] = 5;
    assert!(!is_valid(&grid));
    assert!(solve(&grid).is_none());
    assert_eq!(count_solutions(&grid, 2), 0);
}

#[test]
fn candidates_respect_row_column_and_box() {
    let grid = parse(PUZZLE).unwrap();
    assert_eq!(candidates(&grid, 2), vec![1, 2, 4]);
    assert!(candidates(&grid, 0).is_empty(), "a filled cell has none");
}

#[test]
fn format_round_trips_through_parse() {
    let grid = parse(PUZZLE).unwrap();
    assert_eq!(parse(&format(&grid)).unwrap(), grid);
    assert_eq!(format(&grid).lines().count(), 9);
}
