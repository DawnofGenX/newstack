# {{ title }}

{{ description }}

## Usage

```sh
go build -o bin/app .
./bin/app -add alpha,beta,gamma -has beta,delta
./bin/app -add alpha -del alpha -has alpha
```

`Lookup` returning false is authoritative (no false negatives); a true result can
be a false positive, which is the tradeoff cuckoo filters make for constant
memory per item.
