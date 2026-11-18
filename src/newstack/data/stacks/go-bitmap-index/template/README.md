# {{ title }}

{{ description }}

## Usage

```sh
printf '1
63
64
200
' | go run . -size 256 -query 'rank=64,select=2,has=63'
go test ./...
```

`Bitmap` packs values into `[]uint64` words: `Set`/`Clear`/`Has` are O(1), `Count`
uses `bits.OnesCount64` per word, `Rank(value)` counts set bits strictly below a value
(a prefix sum over whole words plus a masked tail), and `Select(n)` returns the index of
the nth set bit. `Rank(Select(n)) == n` is the invariant the tests pin down.
