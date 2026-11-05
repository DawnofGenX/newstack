# text statistics, with the hot loop in C

A CPython extension module built by setuptools, checked against a pure-Python
reference on random input. `count_bytes` walks the buffer once and returns
`(lines, words, bytes)`.

```
uv venv --allow-existing .venv
uv pip install --python .venv/bin/python -e .
.venv/bin/python -m pytest -q
echo 'a b' | .venv/bin/python -m {{ package_name }}.cli -
```

## Layout

| path | what it is |
| --- | --- |
| `src/{{ package_name }}/_speedups.c` | the extension: `count_bytes`, `count_str`, `separators` |
| `src/{{ package_name }}/reference.py` | the readable implementation the tests compare against |
| `src/{{ package_name }}/cli.py` | `python -m {{ package_name }}.cli [path]` |
| `tests/test_extension.py` | 26 tests: agreement on random bytes, type errors, the `.so` itself |

## Traps this starter already paid for

1. **`y#` is not "any buffer".** It demands a read-only bytes-like object, so a
   `bytearray` raises `TypeError: count_bytes() argument 1 must be read-only
   bytes-like object`. `y*` fills a `Py_buffer`, which accepts `bytes`,
   `bytearray` and `memoryview` alike -- and it carries the length, so embedded
   NUL bytes are counted. `s#` would stop at the first NUL and quietly report a
   truncated size.
2. **`PyBuffer_Release` may clear the struct.** Copy `view.len` into a local
   before releasing, or the size you return afterwards can be zero.
3. **`extra_compile_args` needs `setup.py`.** The `[[tool.setuptools.ext-modules]]`
   table in `pyproject.toml` does not take compile flags portably, and an
   extension compiled without `-Wall -Wextra -Werror` is an extension whose
   refcount bugs ship.
4. **An editable install of an extension is still compiled.** `uv pip install -e .`
   builds `_speedups.c` into `src/{{ package_name }}/_speedups.cpython-*.so`; that file
   must be in `.gitignore`, and deleting it turns every import into
   `ModuleNotFoundError` until you reinstall.
5. **`count_str` must encode, not iterate.** The byte count of `héllo` is 6,
   not 5: the tests assert the UTF-8 length so a future "optimisation" cannot
   quietly switch to `len(str)`.
6. **The reference implementation is the test.** Three fixtures cannot catch a
   separator table that forgets `\v` or `\f`; 200 random byte strings can.
