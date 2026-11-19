# {{ title }}

{{ description }}

## Usage

```sh
printf '1 2 3 4 5\n' | {{ npm_name }}
{{ npm_name }} numbers.txt
```

Exit codes: `0` success, `1` error, `2` usage error.
