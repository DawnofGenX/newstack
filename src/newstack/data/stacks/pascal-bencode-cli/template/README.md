# {{ title }}

{{ description }}

## Usage

```sh
printf 'd1:bi2e1:ai1ee' | {{ npm_name }}
{{ npm_name }} data.benc
```

Exit codes: `0` success, `1` invalid bencode, `2` usage error.
