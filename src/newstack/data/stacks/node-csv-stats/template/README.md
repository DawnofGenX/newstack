# {{ title }}

{{ description }}

## Usage

```sh
npm install
npm test
node src/cli.js --file data.csv
node src/cli.js --file data.csv --table
```

The parser follows RFC 4180 (quoted fields, doubled quotes, embedded newlines and
CRLF line endings) and rejects ragged rows with the offending row number.
