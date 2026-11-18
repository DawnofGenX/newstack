# {{ title }}

{{ description }}

## Run

```sh
{{ package_manager_install }}
mkdir -p content
printf -- '---\ntitle: Hello\n---\n# Body\n' > content/index.md
node src/cli.js --input content --output dist
```

Requires Node {{ node_version }}+.

## Test

```sh
{{ package_manager_test }}
```