# {{ title }}

{{ description }}

## Usage

```sh
go build -o bin/jsonlq .
./bin/jsonlq -file data.jsonl -select name,age -where 'age>=30'
./bin/jsonlq -file data.jsonl -count -where 'age==30'
```