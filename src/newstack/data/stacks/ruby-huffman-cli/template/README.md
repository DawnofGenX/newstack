# {{ title }}

{{ description }}

## Usage

```sh
rake test
./bin/{{ npm_name }} table notes.txt
./bin/{{ npm_name }} encode notes.txt > notes.huff
./bin/{{ npm_name }} decode notes.huff
./bin/{{ npm_name }} stats notes.txt
```

`encode` writes a self-describing payload: the number of code table entries,
one `code "symbol"` line per entry and then the bits themselves, so `decode`
needs nothing else. The tree is built by merging the two lightest nodes, which
gives frequent symbols shorter codes.
