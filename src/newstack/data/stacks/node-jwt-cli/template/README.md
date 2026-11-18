# {{ title }}

{{ description }}

## Usage

```sh
npm install
npm test
node src/cli.js sign --secret s3cr3t --payload '{"sub":"alice"}' --ttl 600
node src/cli.js verify <token> --secret s3cr3t
node src/cli.js decode <token>
```

Only HS256 is accepted: any token advertising another `alg` (including `none`)
is rejected before the signature is checked. `exp` and `nbf` are validated with
an optional `--leeway` in seconds.
