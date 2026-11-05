# {{ title }}

{{ description }}

Configuration is resolved in one place, in a fixed order, and every value carries the
place it came from. That is the whole point: when production disagrees with the repo,
the answer is a command, not an archaeology project.

```
defaults  <  TOML file  <  environment  <  --set flags
```

## Quick start

```bash
uv venv --allow-existing .venv
uv pip install --python .venv/bin/python -e . pytest ruff

export APP_AUTH__SIGNING_KEY="dev-only"
.venv/bin/python -m {{ package_name }} show --config fixtures/config.toml
```

```
server.host                0.0.0.0                            file
server.port                9100                               file
server.timeout             2500                               file
db.url                     ***                                default
db.pool_size               12                                 file
auth.signing_key           ***                                env
auth.token_ttl             1800000                            file
features.rate_limit        true                               default
features.allowed_origins   [https://app.example.com, https://admin.example.com] file
log.level                  warning                            file
```

`--changed` hides the settings nobody touched. `--reveal` prints the secrets. `get`
prints one value raw, and refuses a secret unless you ask for it:

```bash
.venv/bin/python -m {{ package_name }} get log.level --config fixtures/config.toml
# warning
```

`check` is the gate. `--strict` turns "a secret is still the value that shipped with the
code" into exit 1:

```bash
export APP_AUTH__SIGNING_KEY="dev-only"
.venv/bin/python -m {{ package_name }} check --strict
# check  ok: 10 settings, 1 from a layer, 9 at their default
# gate   db.url is still the schema default (sqlite:///app.db) — a secret that ships with the code is not a secret
echo $?   # 1, until APP_DB__URL points at a real database
```

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | the configuration resolved |
| 1 | it resolved, but `check --strict` found a secret at its default |
| 2 | it did not resolve: bad value, unknown key, unreadable file, refused secret |

## The traps this stack is built around

1. **An unset variable and an empty one are different things.** Unset means "no opinion,
   use the next layer"; empty means "I set this to nothing", and for a duration that is a
   parse error rather than a silent fallback.
2. **Precedence is data, not a chain of `if` statements.** `LAYER_ORDER` is a tuple the
   merge folds over, so adding a layer is one line and the order is readable.
3. **Provenance is the feature.** A resolved value without an origin cannot answer the
   question people actually ask, so every value stores its layer *and* its raw location
   (`env APP_SERVER__PORT`, `file /etc/app.toml`).
4. **`bool("false")` is `True`.** Environment text is parsed per declared kind, and a
   boolean accepts only the words that mean something.
5. **`int("1_000")` is `1000`.** The integer parser is a regex on purpose, so a value that
   looks like a number but is not one fails loudly (with a hint) instead of silently
   changing meaning.
6. **Nesting needs a separator that cannot appear in a name.** `_` is legal inside a
   setting, so a dot becomes `__`: `server.port` is `APP_SERVER__PORT`, and a lone
   underscore is reported as a likely typo instead of being ignored.
7. **A printer of resolved configuration is a leak.** Secrets are masked by default,
   `get` refuses them without `--reveal`, and the JSON payload masks them too.
8. **One problem per attempt wastes an afternoon.** Layers are read first and parsed
   afterwards, so a broken file and a bad override are reported together.
9. **An unknown key is a typo, not an extension.** A file key or a prefixed variable the
   schema does not define is an error, because silently ignoring it is how a setting
   appears to work and does not.

## Layout

```
src/{{ package_name }}/spec.py     the schema: kinds, defaults, bounds, secrets
src/{{ package_name }}/sources.py  reading layers and parsing raw values
src/{{ package_name }}/resolve.py  the fold, plus provenance and redaction
src/{{ package_name }}/cli.py      show / get / check / selftest
```
