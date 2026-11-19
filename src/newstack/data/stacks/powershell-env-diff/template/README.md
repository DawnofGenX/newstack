# {{ title }}

Compare two `.env` files structurally. Values are parsed with dotenv quoting
rules (matching single or double quotes, `\n`/`\t` escapes in double quotes,
trailing ` # comment` snippets and an optional `export ` prefix). The core
`Parse-DotEnv` / `Compare-Env` functions take a reader scriptblock, so the CLI
and the test harness share one code path.

## Usage

```sh
./bin/{{ npm_name }} left.env right.env
./bin/{{ npm_name }} --json left.env right.env
./bin/{{ npm_name }} --quiet left.env right.env
pwsh -NoProfile -NonInteractive -File tests/Run-Tests.ps1
```

Text mode prints `+ KEY` for added keys, `- KEY` for removed keys, `~ KEY`
for changed values and `  KEY` for unchanged keys. `--json` emits one compact
object with `added`, `removed`, `changed` and `same` arrays; `--quiet` prints
`differences: N` or `identical`. Exit status is 0 on success, 1 on a read or
parse error, 2 on a usage error.
