# {{ title }}

{{ description }}

A webhook receiver needs to know that a request really came from the sender and
that it is not a replay. This is the Stripe scheme, implemented with the Ruby
standard library only:

- the signed string is `<timestamp>.<raw body>`;
- the digest is `HMAC-SHA256(secret, signed string)`, hex encoded;
- the header carries both halves: `t=1700000000,v1=<hex>`;
- verification recomputes the digest, compares it in constant time, and rejects
  anything outside a tolerance window (300 seconds by default).

## Usage

Sign a payload:

```sh
bin/{{ npm_name }} sign --secret whsec_dev --payload '{"id":1}'
# t=1700000000,v1=2f441ba4b3b2d50d28a9ab9d9fd8880376ecd1eb5d0435401553f5d8d0a5dcf8
```

Sign the body you actually received, straight off stdin:

```sh
signature=$(cat body.json | bin/{{ npm_name }} sign --secret whsec_dev --stdin)
```

Verify a header from an incoming request:

```sh
bin/{{ npm_name }} verify --secret whsec_dev --header "$signature" --stdin < body.json
# ok            (exit 0)
# invalid       (exit 1)
# expired       (exit 1)
# usage message (exit 2)
```

`--now` and `--tolerance` exist so a test can pin the clock: a signature made at
`1700000000` verifies at `--now 1700000300` and is `expired` at `--now 1700000301`.

## Wiring it into a Rack app

```ruby
require 'webhook'

result = Webhook::Signature.verify(
  header: request.env['HTTP_X_SIGNATURE'],
  secret: ENV.fetch('WEBHOOK_SECRET'),
  payload: request.body.read,
  now: Time.now.to_i
)
halt 401 unless result == :ok
```

Read the body **before** handing it to a JSON parser: re-serializing JSON changes
the bytes and the digest stops matching. Return `401` for `:invalid` and `:expired`
alike; log which one so a receiver clock skew shows up in the logs instead of
looking like an attack.

## Layout

```
bin/{{ npm_name }}        thin wrapper that injects the real streams
lib/webhook.rb            requires signature + cli
lib/webhook/signature.rb  sign / verify / constant-time compare (no I/O)
lib/webhook/cli.rb        OptionParser front end with injected io and clock
test/                      minitest: pinned vectors, tolerance edges, exit codes
```

## Tests

```sh
rake test
sh smoke.sh
```

`test/signature_test.rb` pins one digest literal, so an accidental change to the
signed string (the usual way receivers break) fails here rather than in
production.
