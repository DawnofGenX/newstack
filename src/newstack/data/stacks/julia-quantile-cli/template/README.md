# {{ project_name }}

Quantiles and weighted means for a numeric column.

## Usage

```sh
julia --project=. bin/{{ npm_name }}.jl data.txt
julia --project=. bin/{{ npm_name }}.jl data.txt 0.9
julia --project=. bin/{{ npm_name }}.jl --mean data.txt
julia --project=. bin/{{ npm_name }}.jl --weighted-mean pairs.txt
```

Exit codes: 0 success, 1 unreadable input, 2 usage or parse error.