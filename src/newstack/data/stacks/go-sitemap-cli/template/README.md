# {{ title }}

{{ description }}

## Usage

```sh
go vet ./...
go test ./...
go build -o bin/{{ npm_name }} .

bin/{{ npm_name }} -file sitemap.xml
bin/{{ npm_name }} -file sitemap.xml -render
bin/{{ npm_name }} < sitemap.xml
```

The command validates every `<url>` entry: `loc` must be an absolute http(s)
URL without whitespace, `lastmod` must be an RFC 3339 timestamp or a
`YYYY-MM-DD` date, `changefreq` must be one of the seven protocol values, and
`priority` must be a number between 0.0 and 1.0. `-render` prints the
normalised document with the required namespace, and bad input exits 1 while
bad usage exits 2.
