# {{ title }}

A dependency-free HS256 JWT utility in Gleam. The compact token format is
implemented on top of OTP's `crypto` and `base64` modules (reached with
`@external`, so no hex package is fetched); the payload encoder/decoder covers
flat JSON objects of string values. The test suite is a hand-rolled harness,
so `gleam test` needs no third-party test runner.

## Usage

```sh
./bin/{{ npm_name }} --help
./bin/{{ npm_name }} sign whsec_test '{"sub":"alice"}'
./bin/{{ npm_name }} verify whsec_test TOKEN
./bin/{{ npm_name }} claims sub=alice iss=demo
gleam test
```

`sign` prints `base64url(header).base64url(payload).base64url(HMAC-SHA256)`;
`verify` checks the signature and prints the decoded payload; `claims` builds
a flat JSON object from `KEY=VALUE` pairs. Exit status is 0 on success, 1 on
a signature or decode error, 2 on a usage error.
