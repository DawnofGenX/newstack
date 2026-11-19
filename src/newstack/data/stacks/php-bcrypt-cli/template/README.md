# {{ title }}

{{ description }}

bcrypt password hashing and verification from the command line.

## Usage

```console
$ bin/{{ npm_name }} hash secret 4
$2y$04$...
$ bin/{{ npm_name }} verify secret '$2y$04$...'
match
```

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | success or match |
| 1 | mismatch or bad input |
| 2 | usage error |

## Test

```console
$ composer install --no-interaction --prefer-dist && vendor/bin/phpunit
$ bash smoke.sh
```