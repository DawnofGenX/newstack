# {{ title }}

{{ description }}

A fixed-width bitset with the two operations that make a bitset more than a
boolean array: `rank` (how many bits are set below an index) and `select`
(which index holds the n-th set bit). Both are pure functions in
`src/bitset.zig`, so the tests need no allocator and no files.

## Layout

```
build.zig              `zig build` installs the exe, `zig build test` runs both test binaries
build.zig.zon          package manifest (name, version, fingerprint, minimum Zig version)
src/bitset.zig         Bitset: init, set, unset, isSet, count, rank, select
src/main.zig           parse(): argv -> help | usage | config, plus main() and the usage text
```

No dependencies: `build.zig.zon` declares an empty `dependencies` table.

## Usage

```console
$ zig build
$ ./zig-out/bin/{{ package_name }} --len 100 --set 0,1,2,63,64,99 --count
count=6
$ ./zig-out/bin/{{ package_name }} --len 128 --set 0,1,2,63,64 --rank 64
rank[64]=4
$ ./zig-out/bin/{{ package_name }} --len 100 --set 3,70,71 --select 1
select[1]=70
$ ./zig-out/bin/{{ package_name }} --len 200 --set 1,64 --has 64
has[64]=true
```

With no query flag the tool prints the width and the population count:

```console
$ ./zig-out/bin/{{ package_name }} --len 10 --set 4
len=10 count=1
```

`rank` counts the set bits in `[0, index)`, so `rank(0)` is always `0`, and
`select` is 0-based, so `select(rank(i)) == i` for every set bit. That inverse
is asserted in the test suite.

## Exit codes

| code | meaning |
| ---- | ------- |
| 0    | success, including `--help` |
| 1    | an index was outside `0..N` or was not a number |
| 2    | usage error (unknown flag, `--len` missing or zero, flag without a value) |

A set bit never leaks past the requested width: the last word is masked, so
`--len 3` counts at most three bits even if the spare bits of that word are set.

## Test

```console
$ zig build test
```
