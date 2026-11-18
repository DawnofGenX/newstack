# {{ title }}

{{ description }}

## Usage

```sh
printf '1\n4\n9\n' > a.txt
printf '2\n3\n10\n' > b.txt
cargo run -- a.txt b.txt
cargo test
```

The library exposes `merge_sorted(&[Vec<i64>]) -> Vec<i64>` (a min-heap over
`(value, run, position)` so each run is walked exactly once), `parse_block` for
one-integer-per-line files, and `is_sorted` for asserting the result.
