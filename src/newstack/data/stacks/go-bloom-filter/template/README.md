# {{ title }}

{{ description }}

## Usage

```sh
go build -o bin/bloom .
./bin/bloom create filter.json --bits 4096 --hashes 4
./bin/bloom add filter.json hello
./bin/bloom check filter.json hello
./bin/bloom stats filter.json
```
