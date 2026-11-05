# {{ title }}

{{ description }}

A Laravel 13 JSON service on PHP 8.3. Counting lives in a pure class
(`App\Support\TextStat`) with no framework dependency, `StatController` is a
thin route handler, and a PHPUnit 12 suite covers both — including the two
paths a naive starter forgets: a missing field (422) and an unknown route (404).

## Layout

```
composer.json                            PHP ^8.3, Laravel 13, PSR-4 autoloading, PHPUnit 12
bootstrap/app.php                        routes, middleware and exception wiring
routes/web.php                           GET / and GET|POST /count
app/Support/TextStat.php                 pure counting, no I/O
app/Http/Controllers/StatController.php  the HTTP surface
config/                                  the configuration this app actually reads
tests/Unit/TextStatTest.php              counting rules, including empty input
tests/Feature/StatApiTest.php            routes, JSON encoding, 422 and 404 paths
```

## Build

```console
$ composer install
$ cp .env.example .env
```

The first install writes `composer.lock`; commit it so later installs resolve
the same versions.

## Run

```console
$ php artisan serve
```

```console
$ curl 'http://127.0.0.1:8000/'
$ curl 'http://127.0.0.1:8000/count?text=hello%20world'
$ curl -X POST http://127.0.0.1:8000/count \
       -H 'Content-Type: application/json' \
       -d '{"text":"one two\nthree\n"}'
```

Counts follow `wc`: lines are newline characters, words are runs of
non-whitespace, bytes are the raw length.

## Test

```console
$ php artisan test
```

## License

MIT — see [LICENSE](LICENSE).
