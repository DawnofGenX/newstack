# Counting rules

`count_text` answers three questions about one string. The rules are `wc`'s, with
one deliberate difference: the function never touches a device, so it counts a
string you already have.

## Lines

A line ends at a newline character. A trailing newline therefore closes the last
line instead of opening an empty one.

```python
from {{ package_name }} import count_text

print(count_text("a b\nc\n"))
# -> Counts(lines=2, words=3, bytes=6)

print(count_text("hello world\n"))
# -> Counts(lines=1, words=2, bytes=12)
```

## Words

A word is a maximal run of characters that are not whitespace, so any amount of
padding around a word still counts once.

```python
from {{ package_name }} import count_text

print(count_text("  padded  \n"))
# -> Counts(lines=1, words=1, bytes=11)
```

## Bytes

Bytes are UTF-8 bytes, not characters. This is the number you want when you are
budgeting a payload, and the reason the two differ.

```python
from {{ package_name }} import count_text

print(count_text("héllo wörld\n"))
# -> Counts(lines=1, words=2, bytes=14)
```

!!! tip "Empty input is not an error"
    `count_text("")` returns zeros. Only a value that is not a string raises.

```python
from {{ package_name }} import count_text

try:
    count_text(42)
except TypeError as error:
    print(error)
# -> count_text expects a string, got int
```
