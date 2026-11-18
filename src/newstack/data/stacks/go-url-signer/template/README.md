# {{ title }}

{{ description }}

## Usage

```sh
go build -o bin/app .
./bin/app -secret s3cr3t -path /files/report.pdf -ttl 60s
./bin/app -mode serve -secret s3cr3t -addr 127.0.0.1:8080
```

The signature is HMAC-SHA256 over `method \n path \n exp`, carried as `exp` and
`sig` query parameters. Serve mode refuses unsigned or expired requests with 403.
