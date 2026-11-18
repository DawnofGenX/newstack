# {{ title }}

{{ description }}

## Usage

```sh
npm install
npm test
node src/cli.js --file data.ndjson --out-dir parts --max-lines 500
node src/cli.js --file data.ndjson --out-dir parts --max-bytes 1048576
```

Each part is written as `part-0001.ndjson`, `part-0002.ndjson`, ... and the
command prints a JSON summary of the record and chunk counts.
