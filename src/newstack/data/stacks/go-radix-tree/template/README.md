# {{ title }}

{{ description }}

## Usage

```sh
go build -o bin/app .
./bin/app -set romane=1,romanus=2,romulus=3 -get romanus
./bin/app -set api=backend,api/v1=v1 -match api/v1/users
./bin/app -set b=2,a=1 -keys
```

Edges are compressed after the classic radix split on insert, so lookups walk one
node per shared prefix run rather than one node per byte. `-match` returns the
longest stored key that prefixes the given input, which is the shape a router
needs for prefix dispatch.
