# {{ title }}

{{ description }}

## Usage

```sh
npm install --no-audit --no-fund
npm test
node src/cli.js --json config.yaml
node src/cli.js --get server.port config.yaml
cat config.json | node src/cli.js --yaml
```

Supported: block mappings, sequences, `- key: value` items, `[...]`/`{...}`
flow collections, quoted scalars, `#` comments, `---` document markers.
Block scalars (`|`, `>`) and anchors are refused with an explicit error.
