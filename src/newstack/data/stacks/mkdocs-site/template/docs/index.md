# {{ title }}

{{ description }}

This site documents `{{ package_name }}`, a small module that counts lines,
words and bytes the way `wc` does. Every Python example on every page is run by
`tools/check_fences.py` during CI, and the `# ->` lines are the output it
compares against — so the site cannot drift away from the code.

```python
from {{ package_name }} import count_text

print(count_text("hello world\n"))
# -> Counts(lines=1, words=2, bytes=12)
```

Start with [how the counting rules work](guide/counting.md), or jump to the
[API reference](reference/api.md).

!!! note "Why execute the documentation?"
    A doctest inside a docstring only covers what the module author remembered to
    write. This site executes the examples in the Markdown itself, which is the
    copy a reader actually sees.
