# {{ title }}

{{ description }}

## Usage

```sh
npm install
npm test
node src/cli.js hash public/app.js
node src/cli.js hash --algo=sha256 public/app.js
node src/cli.js verify public/app.js 'sha384-...'
node src/cli.js manifest sri.json
```

`sri.json` maps a file path to an integrity string, e.g. `{"app.js": "sha384-..."}`.
