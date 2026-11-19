# {{ title }}

{{ description }}

Deep structural diff of two JSON documents.

## Usage

```console
$ bin/{{ npm_name }} diff '{"a":1}' '{"a":2}'
a: 1 -> 2
$ bin/{{ npm_name }} diff '{"a":1}' '{"a":1}'
no differences
```

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | no differences |
| 1 | differences found or bad input |
| 2 | usage error |

## Test

```console
$ rake test
$ bash smoke.sh
```