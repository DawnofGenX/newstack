# {{ title }}

{{ description }}

## Usage

```sh
go build -o bin/app .
./bin/app compare 1.2.3 1.10.0
./bin/app satisfies 1.9.0 '^1.2.0'
```

Supported constraints: `*`, exact versions, `=`, `>`, `>=`, `<`, `<=`, caret
(`^1.2.3`), tilde (`~1.2`) and x-ranges (`1.2.x`). Prerelease versions order below
their release, per the semver specification.
