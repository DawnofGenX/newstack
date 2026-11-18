# {{ title }}

{{ description }}

## Usage

```sh
cargo run -- --capacity 5 --rate 2 --requests 8 --interval-ms 400
cargo test
```

The bucket takes an explicit millisecond clock on every call, so tests never sleep
and the refill maths is reproducible. `time_until` reports how long a caller has
to wait, and `None` when the requested burst exceeds capacity.
