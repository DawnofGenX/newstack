# {{ npm_name }}

A small tracing service with JSON log output and smoke checks on its log lines.

```bash
cargo fmt --check
cargo clippy --all-targets -- -D warnings
cargo test
cargo build --release
bash smoke.sh
```
