use {{ package_name }}::{is_sorted, merge_sorted, parse_block};

#[test]
fn merges_two_runs() {
    let merged = merge_sorted(&[vec![1, 4, 9], vec![2, 3, 10]]);
    assert_eq!(merged, vec![1, 2, 3, 4, 9, 10]);
}

#[test]
fn merges_many_runs_with_duplicates() {
    let merged = merge_sorted(&[vec![1, 1], vec![1, 2], vec![0, 5], vec![]]);
    assert_eq!(merged, vec![0, 1, 1, 1, 2, 5]);
    assert!(is_sorted(&merged));
}

#[test]
fn empty_input_yields_empty_output() {
    assert_eq!(merge_sorted(&[]), Vec::<i64>::new());
    assert_eq!(merge_sorted(&[vec![], vec![]]), Vec::<i64>::new());
}

#[test]
fn single_run_is_returned_unchanged() {
    let run = vec![-3, -1, 0, 7];
    assert_eq!(merge_sorted(std::slice::from_ref(&run)), run);
}

#[test]
fn payloads_wider_than_a_u8_are_kept_in_order() {
    let merged = merge_sorted(&[vec![i64::MIN, 0], vec![i64::MAX], vec![-1]]);
    assert_eq!(merged, vec![i64::MIN, -1, 0, i64::MAX]);
}

#[test]
fn parse_block_skips_blanks_and_reports_bad_lines() {
    assert_eq!(parse_block("1\n\n3\n"), Ok(vec![1, 3]));
    let error = parse_block("1\nx\n").unwrap_err();
    assert_eq!(error, "line 2 is not an integer: \"x\"");
}
