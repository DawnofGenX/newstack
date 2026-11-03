# {{ title }}

{{ description }}

A small PHP 8.3 Symfony 7 web app: the counting lives in a pure service
(`TextStats`) so tests drive it directly, and `HomeController` is a thin route
that injects the service and returns a JSON response. Symfony's front
controller, DI container and routing do the rest; PHPUnit runs the suite.

## Layout

```
composer.json                      PHP ^8.3, Symfony 7, PSR-4 autoloading, PHPUnit 11
phpunit.xml                        test suite configuration
public/index.php                   front controller
bin/console                        Symfony console entry point
config/                            bundles, services, routes and framework config
src/Kernel.php                     micro-kernel
src/Controller/HomeController.php  GET / -> JSON response
src/Service/TextStats.php          pure counting, no I/O
src/Service/Stats.php              line / word / byte value object
tests/                             PHPUnit 11 unit + functional tests
```

## Build

```console
$ composer install
```

The first install writes `composer.lock`; commit it so later installs resolve
the same versions.

## Run

```console
$ php -S localhost:8000 -t public
$ curl http://localhost:8000/
```

The route returns JSON: the message plus its line / word / byte counts.

## Console

```console
$ php bin/console about
```

## Test

```console
$ vendor/bin/phpunit
```

## License

MIT — see [LICENSE](LICENSE).
