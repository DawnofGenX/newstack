# {{ title }}

{{ description }}

## Usage

```sh
printf 'foobar' | php bin/{{ npm_name }} encode
printf 'MZXW6YTBOI======' | php bin/{{ npm_name }} decode
printf 'foobar' | php bin/{{ npm_name }} encode --no-pad --crockford
vendor/bin/phpunit
```

`Base32::encode` / `Base32::decode` implement RFC 4648 with padding, and the
`Crockford` variants use the 0-9A-Z alphabet without I, L, O and U, normalising those
lookalikes on decode so identifiers typed by hand still resolve.

## Layout

`src/Base32.php` is the codec, `src/Cli.php` the stdin/argv front end, `bin/{{ npm_name }}`
the entry point. Tests cover the seven RFC 4648 vectors plus padding, whitespace,
lookalike and error-path behaviour.
