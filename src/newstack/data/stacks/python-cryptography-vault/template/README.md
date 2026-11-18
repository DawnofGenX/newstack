# {{ title }}

{{ description }}

Requires Python {{ python_version }} or newer.

## Run

```bash
uv venv --allow-existing .venv && uv pip install -e . pytest ruff
.venv/bin/python -m {{ package_name }} encrypt secret.txt --password pw
```

## Check

```bash
.venv/bin/python -m {{ package_name }} --selftest
.venv/bin/python -m pytest
bash smoke.sh
```

## Traps this starter already paid for

- Key is derived with PBKDF2-HMAC-SHA256 and a fresh salt per entry.
- Fernet provides authenticated encryption; tampering raises `InvalidToken`.
- Manifest stores salt and ciphertext filename, never the password.
- Wrong password fails closed with a non-zero exit code.
