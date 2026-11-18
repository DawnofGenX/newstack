# {{ title }}

{{ description }}

## Usage

```sh
composer install
php -S 127.0.0.1:5577 -t public public/index.php
curl http://127.0.0.1:5577/health
```

## Test

```sh
vendor/bin/phpunit
```
