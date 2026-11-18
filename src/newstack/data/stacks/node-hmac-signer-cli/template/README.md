# {{ title }}

{{ description }}

## Usage

```sh
npm install
npm test
node src/cli.js sign --secret mysecret --payload "hello" --timestamp 1700000000
node src/cli.js verify --secret mysecret --payload "hello" --signature "v1=..." --timestamp 1700000000
```
