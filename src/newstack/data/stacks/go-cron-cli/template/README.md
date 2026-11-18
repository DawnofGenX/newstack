# {{ title }}

{{ description }}

## Usage

```sh
go build -o bin/{{ npm_name }} .
./bin/{{ npm_name }} -spec "*/15 * * * *" -count 4
./bin/{{ npm_name }} -spec "0 9 * * 1-5" -from 2024-01-05T10:00:00Z -count 3
```
