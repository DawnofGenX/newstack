# {{ title }}

{{ description }}

## Usage

```sh
cargo test
cargo run --release -- --grid 530070000600195000098000060800060003400803001700020006060000280000419005000080079
cargo run --release -- --candidates 2 --grid 53007000
```

The puzzle is 81 digits where `0` or `.` marks an empty cell; whitespace is
ignored, so a pretty board works too. `--count` reports up to two solutions and
`--candidates N` lists the digits legal for a cell. Contradictory puzzles exit 1.
