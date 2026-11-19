# {{ title }}

{{ description }}

## Usage

```sh
{{ npm_name }} input.json
{{ npm_name }} < input.json
echo '{"b":2,"a":1}' | {{ npm_name }}
```

Exit codes: `0` success, `1` invalid JSON, `2` usage error.

## Install

```sh
make install
```
