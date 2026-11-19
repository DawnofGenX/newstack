# {{ title }}

A Haxe/Neko Mustache template renderer.

## Build

```sh
make
make test
```

## Usage

```sh
./bin/{{ npm_name }} TEMPLATE DATA.json
printf '{"name":"world"}' | ./bin/{{ npm_name }} template.mustache -
./bin/{{ npm_name }} --help
./bin/{{ npm_name }} --version
```

Exit codes: `0` success, `1` read/parse error, `2` usage error.

### Example

template.mustache:

```
Hello {{!name}}!
{{!#items}}
- {{!.}}
{{!/items}}
```

data.json:

```json
{"name":"world","items":["a","b"]}
```

Render:

```sh
$ ./bin/{{ npm_name }} template.mustache data.json
Hello world!
- a
- b
```

Unescaped: `{{!{raw}}}` or `{{!&raw}}`. Inverted sections: `{{!^list}}empty{{!/list}}`.
Comments: `{{!! this is ignored }}`.
Partials: `{{!> partial}}` loads `partial.mustache` from the working directory.

## License

MIT
