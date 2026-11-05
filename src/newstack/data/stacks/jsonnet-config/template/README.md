# {{ project_name }}

{{ description }}

A service manifest written in [Jsonnet](https://jsonnet.org/): the manifest is data,
the rules are data, and the test suite is data. Three commands compile it, validate it
and prove the rules still reject what they should.

## Requirements

- Jsonnet 0.20 or newer (`apt-get install jsonnet` on Debian and Ubuntu)
- `make` (optional, but the workflows use it)

## Quick start

```sh
make build        # build/manifest.json
./bin/{{ npm_name }} check   # ok, or the list of problems
./bin/{{ npm_name }} test    # 18 checks
```

## What it does

```
$ ./bin/{{ npm_name }} check
ok
$ ./bin/{{ npm_name }} render | head -8
{
   "serviceNames": [
      "gateway",
      "scheduler",
      "worker"
   ],
```

`render` compiles `config/manifest.jsonnet` into the document a deploy step would
consume: services sorted by name, each with its image, port, replicas and env, plus
the total replica count. `check` runs `lib/schema.libsonnet` over the manifest and
prints either `ok` or one line per problem.

## The rules

| Rule | Why |
| ---- | --- |
| name is 1–63 characters, starts with a lower-case letter, then letters, digits or dashes | it becomes a DNS label |
| image is a non-empty string | an empty image deploys nothing |
| port is 1–65535 | a port outside the range is never reachable |
| replicas is 1–20 | zero replicas silently removes a service, and a large number is a typo |
| every `env` value is a string | a number or object in `env` renders as the wrong type |
| names are unique | two services with one name overwrite each other |
| at least one service | an empty manifest is almost always a mistake |

## Layout

```
config/manifest.jsonnet   the manifest
config/render.jsonnet     compile it
config/check.jsonnet      validate it
lib/schema.libsonnet      the rules, as functions returning errors
lib/render.libsonnet      the rendering, sorted and summed
tests/                    18 checks over both libraries, in Jsonnet
```

## Testing

```sh
./bin/{{ npm_name }} test
```

The suite builds deliberately broken manifests and asserts that each rule fires with a
message that names the rule, so a validator that silently accepts everything fails the
suite rather than passing it.

## A note on validation

`std.findSubstr` in Jsonnet ignores `^` and `$`, so a regex such as
`^[a-z][a-z0-9-]*$` matches nothing at all. The name check is therefore written
character by character against `std.stringChars`.
