# {{ title }}

{{ description }}

## Usage

```sh
dart pub get
dart run bin/{{ npm_name }}.dart data.csv
dart run bin/{{ npm_name }}.dart -c city,name --json data.csv
cat data.tsv | dart run bin/{{ npm_name }}.dart -d tab
```

The parser follows RFC 4180: doubled quotes, quoted delimiters and newlines
inside fields, CRLF line endings. `-c` takes header names or 1 based positions.
