# {{ title }}

{{ description }}

## Usage

```sh
mix deps.get
mix test
MIX_ENV=prod mix escript.build && ./{{ npm_name }} --help
```
