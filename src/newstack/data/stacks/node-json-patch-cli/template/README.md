# {{ title }}

{{ description }}

## Usage

```sh
npm install
npm test
echo '{"foo":1}' > /tmp/doc.json
echo '[{"op":"add","path":"/bar","value":2}]' > /tmp/patch.json
node src/cli.js apply /tmp/doc.json /tmp/patch.json
```