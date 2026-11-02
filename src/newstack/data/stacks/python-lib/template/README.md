# {{ title }}

{{ description }}

## Install

```bash
uv sync
```

## Use

```python
from {{ package_name }} import truncate, word_count

word_count("hello world")   # 2
truncate("hello world", 8)  # "hello w…"
```

## Develop

```bash
uv run pytest        # tests
uv run ruff check .  # lint
uv build             # sdist + wheel
```

Generated with [newstack](https://github.com/DawnofGenX/newstack).
