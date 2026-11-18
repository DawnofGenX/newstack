# {{ npm_name }}

{{ description }}

A small TOML reader with no dependencies: strings, integers and floats,
booleans, arrays, tables, arrays of tables, dotted keys and inline tables, with
every error reported as `line N: ...`.

## Usage

```bash
# render a file as JSON
{{ npm_name }} config.toml

# read TOML from stdin
cat config.toml | {{ npm_name }}

# pull out one value
{{ npm_name }} --get server.host config.toml
{{ npm_name }} --get server.ports[0] config.toml

# one dotted key=value per line, handy for diffing
{{ npm_name }} --flatten config.toml
```

Exit codes: `0` success, `1` unreadable file or invalid TOML, `2` bad usage.

Library use is the same parser:

```ts
import { parseToml, flatten, getPath } from "./src/toml/toml.ts";

const config = parseToml(await Bun.file("config.toml").text());
console.log(getPath(config, "server.host"));
```

Dates are refused on purpose — `1979-05-27` is a string, a number and a
subtraction at once, so quote the value if it is text.
