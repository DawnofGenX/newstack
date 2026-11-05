# {{ title }}

A JSON service in Dart built on [shelf](https://pub.dev/packages/shelf). One counting contract,
three shapes of surface: a pure library, a `Handler` you can call directly in a test, and a
socket you can curl.

## Requirements

- Dart 3.5 or newer (`dart --version`)
- `curl`, for the smoke test

## Layout

```
bin/{{ npm_name }}.dart        entry point: PORT/ADDR, graceful stop on SIGINT/SIGTERM
lib/src/counts.dart        Counts + countText — no shelf, no HTTP
lib/src/handler.dart       buildHandler(): routing and JSON, returns a Handler
test/counts_test.dart      the counting table
test/handler_test.dart     the routes, driven in-process
```

## Run it

```sh
dart pub get
PORT=8080 dart run bin/{{ npm_name }}.dart

curl 'http://127.0.0.1:8080/health'
curl 'http://127.0.0.1:8080/stats?text=hello%20world%0A'
curl -X POST -H 'content-type: application/json' \
     --data-binary '{"text":"a b\nc\n"}' http://127.0.0.1:8080/stats
```

`GET /stats` answers with the text it counted plus `lines`, `words` and `bytes`. FastAPI-style
rules apply: a missing `text` parameter is a `422`, an unparseable body is a `422` (not a `500`),
and an unknown path is a JSON `404`.

Counting matches `wc`: a line ends at `\n`, a word is a maximal run of non-space characters, and
`bytes` is the UTF-8 length — `héllo` is 5 characters and 6 bytes.

## Test it

```sh
dart test
```

`buildHandler()` returns a `Handler`, which is just `Future<Response> Function(Request)`. The
tests call it with a constructed `Request`, so there is no port, no bind, no readiness loop and
no chance of a flaky `SocketException` on a busy CI machine. The verify step still boots the
real server: a handler that only works in-process is a handler that fails in production.

## Notes

- `pubspec.lock` is not shipped in the template. It is not gitignored either — commit the lock
  file once `dart pub get` has produced one, so deploys use the versions you tested.
- `dart analyze --fatal-infos` is the gate, not just `dart analyze`: the lint set is
  `package:lints/recommended.yaml`, and its warnings are what keep the code honest.
