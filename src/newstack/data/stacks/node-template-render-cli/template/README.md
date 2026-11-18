# {{ title }}

{{ description }}

A template is plain text with placeholders; the syntax lives in
[docs/SYNTAX.md](docs/SYNTAX.md).

## Usage

```sh
npm install
npm test
echo '{"name":"Ada","count":2,"noun":"messages"}' > context.json
$EDITOR template.tpl        # see docs/SYNTAX.md for the placeholders
node src/cli.js template.tpl context.json
```
