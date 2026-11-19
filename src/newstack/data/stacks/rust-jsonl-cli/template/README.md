# {{ title }}

{{ description }}

## Usage

```sh
cargo build --release
./target/release/{{ npm_name }} -file data.jsonl -select name -where 'age==30'
```