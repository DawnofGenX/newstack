# {{ npm_name }}

A labstack/echo JSON service with httptest tests and a curl smoke check.

```bash
go test ./...
go build -o {{ npm_name }} .
PORT=5512 ./{{ npm_name }}
bash smoke.sh
```
