# {{ npm_name }}

{{ description }}

HMAC signing and verification over UTF-8 text or a file, with constant-time
comparison so a mismatch cannot leak the expected digest byte by byte.

## Usage

```bash
# sign a message
{{ npm_name }} sign --key s3cret --message 'hello'

# verify it (exits 0 on match, 1 on mismatch)
{{ npm_name }} verify --key s3cret --message 'hello' --digest <hex>

# sign a file and print `<digest>  <path>`
{{ npm_name }} sign-file --key s3cret release.tar.gz

# pick another algorithm
{{ npm_name }} sign --key s3cret --message 'hello' --algo sha512
```

Algorithms: `sha256` (default), `sha384`, `sha512`, `sha1`, `md5`.
Exit codes: `0` ok or matched, `1` mismatch or unreadable file, `2` bad usage.
