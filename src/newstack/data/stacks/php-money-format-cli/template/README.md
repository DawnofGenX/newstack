# {{ title }}

{{ description }}

Money formatting and allocation from the command line.

## Usage

```console
$ bin/{{ npm_name }} format 12.34
$12.34
$ bin/{{ npm_name }} allocate 1.00 3
0.34,0.33,0.33
```

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | success |
| 1 | bad input |
| 2 | usage error |

## Test

```console
$ composer install --no-interaction --prefer-dist && vendor/bin/phpunit
$ bash smoke.sh
```
