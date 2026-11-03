# {{ title }}

{{ description }}

A small JSON API on [Sinatra](https://sinatrarb.com), in modular style: `app.rb`
defines `App < Sinatra::Base`, `config.ru` boots it, and the RSpec suite drives it
in-process through `rack-test` — no socket, no port, no sleeping server.

## Requirements

- Ruby 3.2+
- Bundler (`gem install bundler`)
- A C toolchain, for the native extensions in `json`, `nio4r` and `prism`
  (`ruby-dev` on Debian/Ubuntu, Xcode command line tools on macOS)

## Setup

```bash
bundle install
```

Gems go to `vendor/bundle` because `.bundle/config` sets `BUNDLE_PATH`, so nothing
is installed system-wide and `sudo` is never needed. That is also the directory
`ruby/setup-ruby` caches in CI, so local and CI resolve the same way.

## Run

```bash
bundle exec puma -p 4567
```

Then:

```bash
curl http://127.0.0.1:4567/health          # {"status":"ok"}
curl http://127.0.0.1:4567/greet/ada       # {"message":"Hello, ada!"}
curl -X POST http://127.0.0.1:4567/echo \
  -H 'Content-Type: application/json' -d '{"hello":"world"}'
# {"received":{"hello":"world"}}
```

## Routes

| Method | Path | Response |
| --- | --- | --- |
| GET | `/health` | `{"status":"ok"}` |
| GET | `/greet/:name` | `{"message":"Hello, <name>!"}` |
| POST | `/echo` | `{"received": <posted JSON>}` |

Unknown routes answer `404` with `{"error":"not found"}`; a body that is not JSON
gets `400` with `{"error":"invalid JSON"}`. Every response is `application/json`.

## Test

```bash
bundle exec rspec
```

The suite covers the 200 paths, the JSON shape of each response, the invalid-body
`400`, and the `404`. `rack-test` calls the Rack app directly, so the tests are
fast and never collide over a port.

## Lint

```bash
bundle exec rubocop
```

## Layout

```
app.rb               Sinatra::Base subclass and routes
config.ru            Rack entrypoint (run: `bundle exec puma`)
spec/spec_helper.rb  rack-test wired into RSpec
spec/app_spec.rb     route behaviour
.github/workflows/ci.yml  RuboCop + RSpec on Ruby 3.2 and 3.3
```

## License

MIT — see [LICENSE](LICENSE).
