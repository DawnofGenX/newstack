use std::io::Cursor;

use {{ package_name }}::analyze_reader;

#[test]
fn computes_per_column_stats() {
    let csv = "a,b\n1,2\n3,4\n1,5\n";
    let stats = analyze_reader(Cursor::new(csv)).unwrap();
    assert_eq!(stats.len(), 2);
    assert_eq!(stats[0].name, "a");
    assert_eq!(stats[0].count, 3);
    assert_eq!(stats[0].min, Some(1.0));
    assert_eq!(stats[0].max, Some(3.0));
    assert_eq!(stats[0].mean, Some(5.0 / 3.0));
    assert_eq!(stats[0].unique, 2);
    assert_eq!(stats[1].unique, 3);
}
