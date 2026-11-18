# {{ title }}

{{ description }}

## Usage

```sh
composer install
vendor/bin/phpunit

php bin/{{ npm_name }} get /nested/id doc.json          # 3
php bin/{{ npm_name }} has /tags/1 doc.json            # exit 0
php bin/{{ npm_name }} set /name --value '"renamed"' doc.json
php bin/{{ npm_name }} remove /tags/0 doc.json
php bin/{{ npm_name }} tokens /a~1b/m~0n doc.json      # ["a/b","m~n"]
```

Pointers are RFC 6901: the empty string addresses the document root, `/` splits
reference tokens, `~1` is a literal slash and `~0` a literal tilde. `set` follows
RFC 6902 add semantics (`-` appends to an array), and `remove` prints the removed
value. Unknown commands or options exit 2, unresolvable pointers exit 1.
