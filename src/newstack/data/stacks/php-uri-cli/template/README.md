# {{ title }}

{{ description }}

URIs look like strings but are a small grammar, and the parts that bite are not
the obvious ones: port 80 is not part of a URL's identity, `/a/./b/../c` is not
four path segments, and `?a=1&a=2` is a key with two values. This tool exposes
each of those decisions instead of hiding them.

## Layout

```
src/Uri.php      parse, toString, normalize, removeDotSegments, query pairs
src/Cli.php      parse | normalize | encode | decode | query
tests/           PHPUnit: component parsing, normalisation, query merging, CLI codes
bin/             the executable (needs vendor/ from composer install)
```

## Usage

```console
$ composer install
$ php bin/{{ npm_name }} normalize 'HTTP://Example.COM:80/a/./b/../c'
http://example.com/a/c
$ php bin/{{ npm_name }} parse 'https://user:secret@example.com:8443/a?x=1#top'
{"scheme":"https","user":"user","password":"secret","host":"example.com","port":8443,"path":"/a","query":"x=1","fragment":"top"}
$ php bin/{{ npm_name }} query 'https://example.com/a?x=1&y=2' y=9 z=3
https://example.com/a?x=1&y=9&z=3
$ php bin/{{ npm_name }} encode 'a b&c'
a%20b%26c
$ php bin/{{ npm_name }} decode 'a%20b%26c'
a b&c
```

## What normalisation changes

| input | output | why |
| ----- | ------ | --- |
| `HTTP://Example.COM:80/a` | `http://example.com/a` | scheme and host are case-insensitive; 80 is the default |
| `https://example.com:443/a` | `https://example.com/a` | same for 443 |
| `http://example.com:8080/a` | `http://example.com:8080/a` | 8080 is not the default, so it stays |
| `https://example.com` | `https://example.com/` | an empty path with a host is `/` |
| `/a/./b/../c` | `/a/c` | RFC 3986 section 5.2.4 |

## Query parameters

Parameters keep their order, a bare key (`?flag`) is preserved as an empty
value, and `query` replaces in place while appending anything new. `?a=1&a=2` is
two values for one key, which the replace path collapses to the new value.

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | success, including `--help` |
| 1 | an unexpected runtime failure |
| 2 | usage error: no command, an unknown command, the wrong argument count, a bad `KEY=VALUE`, a port out of range |

## Test

```console
$ vendor/bin/phpunit
$ bash smoke.sh
```
