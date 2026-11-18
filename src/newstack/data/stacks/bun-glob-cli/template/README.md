# {{ npm_name }}

{{ description }}

A glob matcher and a tiny `find`: `*`, `**`, `?`, `[abc]`, `[!abc]` and
`{a,b}` alternatives, with no dependencies and no surprises about anchoring
(the whole path must match).

## Usage

```bash
# every TypeScript file, at any depth
{{ npm_name }} '**/*.ts'

# from another directory, skipping one subtree
{{ npm_name }} --root ../project --ignore 'node_modules/**' '**/*.{ts,js}'

# NUL-separated output for xargs
{{ npm_name }} -0 'src/**/*.ts' | xargs -0 wc -l
```

Exit codes: `0` at least one match, `1` no match or unreadable root, `2` bad
usage.

The matcher is usable on its own:

```ts
import { matches, globToRegExp } from "./src/glob/glob.ts";

matches("**/*.ts", "src/deep/a.ts"); // true
globToRegExp("*.{js,ts}").test("index.ts"); // true
```
