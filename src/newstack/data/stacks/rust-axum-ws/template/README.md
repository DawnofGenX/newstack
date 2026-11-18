# {{ title }}

{{ description }}

## Run

```sh
cargo run
```

Then in another terminal:

```sh
curl http://127.0.0.1:5552/health
```

Requires Rust (stable). The WebSocket endpoint is `/ws`.

## Test

```sh
cargo test
```