# {{ title }}

{{ description }}

## Usage

```sh
go build -o bin/{{ npm_name }} .
./bin/{{ npm_name }}
curl -X POST http://127.0.0.1:5592/webhook -H 'Content-Type: application/json' -d '{"msg":"hi"}'
```
