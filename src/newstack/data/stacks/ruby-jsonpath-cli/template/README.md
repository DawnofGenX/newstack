# {{ title }}

{{ description }}

## Usage

```sh
echo '{"a":[{"b":1},{"b":2}]}' | bin/{{ npm_name }} '$.a[*].b'
bin/{{ npm_name }} --count '$..price' store.json
bin/{{ npm_name }} --help
rake test
```

The supported subset is `$`, `.name`, `['name']`, `[0]`, `[-1]`, `.*`, `[*]`, `..name` and
`..*` — enough for configuration and fixture traversal without a dependency. Exit status is
`0` when something matched, `1` when nothing did, `2` for bad usage and `3` for input that is
not readable JSON, so the CLI composes in shell pipelines.

## Layout

`lib/jsonpath/query.rb` compiles a path into steps once and evaluates them over the document;
`lib/jsonpath/cli.rb` is the stdin/argv front end.
