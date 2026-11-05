# API reference

## `Counts`

A frozen dataclass with three integer fields, in `wc`'s order.

| Field | Meaning |
| --- | --- |
| `lines` | number of `\n` characters |
| `words` | number of maximal non-whitespace runs |
| `bytes` | length of the UTF-8 encoding |

## `count_text(text: str) -> Counts`

```python
from {{ package_name }} import Counts, count_text

counts = count_text("one two\nthree\n")
print(counts == Counts(lines=2, words=3, bytes=14))
# -> True
```

The function is pure: same input, same output, no I/O. It raises `TypeError`
when `text` is not a `str`, which keeps the failure at the call site instead of
deep inside a byte-counting loop.
