# {{ title }}

{{ description }}

A dependency-free Rust command line tool: the parsing and greeting logic live
in a library (`src/lib.rs`) so they can be unit tested, and `src/main.rs` is a
thin binary that turns a [`Command`] into output and an exit code.

## Layout

```
src/lib.rs        greet + parse + unit tests
src/main.rs       binary: prints the greeting or version, exit code 2 on bad input
tests/cli.rs      integration tests over the public API
```

No third-party crates — argument parsing is hand-rolled with the standard
library.

## Run

```console
$ cargo run -- greet --name you
Hello, you!

$ cargo run -- --version
0.1.0
```

## Test

```console
$ cargo test
```

## Build

```console
$ cargo build --release
```

The release binary is at `target/release/{{ npm_name }}`.

## License

MIT — see [LICENSE](LICENSE).
