# {{ title }}

{{ description }}

## Usage

```sh
dart pub get
dart test

dart run bin/{{ npm_name }} data.json          # {"a":[3,1],"b":2}
cat data.json | dart run bin/{{ npm_name }}    # stdin works the same way
dart run bin/{{ npm_name }} --pretty data.json # indented, still sorted
dart run bin/{{ npm_name }} --check data.json  # exit 1 when not canonical
```

Object keys are sorted by UTF-16 code unit, whitespace is dropped entirely and
numbers lose a redundant fraction, so `2.0` prints as `2` and `-0.0` as `0`.
Values JSON cannot represent (NaN, infinity, non-string keys) are refused with
a message instead of being silently rewritten. Exit codes: 0 success, 1
unreadable input or a failed `--check`, 2 bad usage.
