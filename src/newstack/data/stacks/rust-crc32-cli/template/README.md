# {{ title }}

{{ description }}

## Usage

```sh
printf '123456789' | cargo run --quiet
printf '123456789' | cargo run --quiet -- --crc32c
cargo run --quiet -- some-file.bin
cargo test
```

`Crc32::ieee()` and `Crc32::castagnoli()` build the same table-driven core from a different
polynomial, so `crc32("123456789")` is `cbf43926` and `crc32c("123456789")` is `e3069283` —
the check values both specifications publish. `update` is incremental and `finish` is
idempotent, so streaming a large file never buffers it.
