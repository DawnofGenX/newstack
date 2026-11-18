# {{ title }}

{{ description }}

## Usage

```sh
composer install
php src/main.php '<p onclick="x()">hi</p><script>alert(1)</script>'
vendor/bin/phpunit
```

The allowlist lives in `Sanitizer::ALLOWED` (tag => attributes). Anything not on
it is unwrapped so the text survives; `script`, `style`, `iframe`, `object`,
`embed`, `noscript` and `template` are removed with their contents;
`javascript:`, `vbscript:` and `data:` hrefs are dropped; every `target="_blank"`
link gains `rel="noopener noreferrer"`.
