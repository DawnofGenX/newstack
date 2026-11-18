# {{ title }}

{{ description }}

## Usage

```sh
npm install
npm test
node src/cli.js --file .env
node src/cli.js --file .env --allowExtra
```

The schema lives in `src/cli.js`; `src/schema.js` exports `parseDotEnv`,
`coerce` and `validateEnv` so you can reuse it with your own keys.
