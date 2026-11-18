# {{ title }}

{{ description }}

## Usage

```sh
swift build
swift test

./bin/{{ npm_name }} --to 2024          # MMXXIV
./bin/{{ npm_name }} --from MCMXC       # 1990
./bin/{{ npm_name }} 14 XIV             # converts both, auto-detected
printf '9\nXL\n' | ./bin/{{ npm_name }}  # reads one value per line
```

Only the classical range 1...3999 is accepted, and parsing is strict: `IIII`,
`VV` and `IC` are rejected with a message naming the canonical form. Unknown
options exit 2, bad input exits 1.
