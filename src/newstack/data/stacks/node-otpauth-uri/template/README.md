# {{ title }}

{{ description }}

## Usage

```sh
npm install
npm test
node src/cli.js uri --secret JBSWY3DPEHPK3PXP --issuer Acme --account alice@example.com
node src/cli.js code --secret JBSWY3DPEHPK3PXP
node src/cli.js code --secret JBSWY3DPEHPK3PXP --time 1700000000 --digits 8
node src/cli.js parse 'otpauth://totp/Acme:alice%40example.com?secret=JBSWY3DPEHPK3PXP'
```
