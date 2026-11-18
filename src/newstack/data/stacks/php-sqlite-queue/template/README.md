# {{ title }}

Durable SQLite job queue.

## Usage

```sh
composer install
php bin/queue push "job payload"
php bin/queue pop --lease 30
php bin/queue ack 1
```
