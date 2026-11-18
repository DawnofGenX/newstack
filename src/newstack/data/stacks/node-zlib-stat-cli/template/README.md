# {{ title }}

{{ description }}

## Usage

```sh
npm install
npm test

node src/cli.js compress notes.txt --level 9 --out notes.txt.gz
node src/cli.js decompress notes.txt.gz --out notes.copy.txt
node src/cli.js stats notes.txt.gz
node src/cli.js stats notes.txt.gz --json
```

`stats` prints `input=N bytes compressed=M bytes ratio=R saved=S bytes`, where the
ratio is the compressed size divided by the original size rounded to three
decimals. Compression levels run from 0 (stored) to 9 (smallest), and the
command exits 2 on bad usage, 1 on an unreadable file or corrupt gzip stream.
