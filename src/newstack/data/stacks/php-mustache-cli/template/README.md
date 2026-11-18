# {{ title }}

{{ description }}

## Usage

```sh
composer install
vendor/bin/phpunit
php bin/{{ npm_name }} page.mustache --data data.json
printf 'Hi Ada' | php bin/{{ npm_name }} --json '{"name":"Ada"}'
```

The renderer supports variables, HTML-escaped and raw tags, sections and
inverted sections, dotted member names, the implicit iterator and comments.
Partials are refused with an explicit error rather than silently ignored.

See `docs/SYNTAX.md` for the tag syntax with worked examples.
