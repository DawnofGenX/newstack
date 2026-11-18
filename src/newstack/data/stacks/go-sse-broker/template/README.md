# {{ title }}

{{ description }}

## Usage

```sh
go build -o bin/ssebroker .
./bin/ssebroker
curl -N http://localhost:5580/events
curl -X POST http://localhost:5580/publish -d '{"message":"hi"}'
```
