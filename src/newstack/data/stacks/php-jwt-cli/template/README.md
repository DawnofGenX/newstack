# {{ title }}

HS256 JWT sign/verify CLI.

## Usage

```sh
composer install
php src/main.php sign secret '{"sub":"alice","exp":1700000000}'
php src/main.php verify secret <token>
vendor/bin/phpunit
```
