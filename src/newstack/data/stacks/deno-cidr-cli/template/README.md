# {{ title }}

{{ description }}

## Usage

```sh
deno task test
printf '10.1.2.3/8\n192.168.0.0/16\n' | ./bin/{{ npm_name }}
./bin/{{ npm_name }} --contains 192.168.4.4 --json blocks.txt
```

Each input line is `address/prefix`; `#` starts a comment. The table shows the
canonical block, its network and broadcast address and the usable host count.
