# {{ title }}

{{ description }}

## Usage

```sh
cargo build --release
./target/release/{{ npm_name }} '(+ 1 2 3)'
./target/release/{{ npm_name }} '(if (< 1 2) (list 1 2) nil)'
echo '(len "abc")' | ./target/release/{{ npm_name }}
```
