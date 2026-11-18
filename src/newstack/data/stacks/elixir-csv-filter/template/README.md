# {{ title }}

{{ description }}

A small Elixir command line tool that filters CSV rows by a column value.
Parsing and filtering live in pure modules (`CsvFilter.Options`,
`CsvFilter.Filter`) so ExUnit drives them directly, and `CsvFilter.CLI` is a
thin shell around argv, output and the exit code. `escript` turns it into a
single runnable binary, no runtime dependencies.

## Usage

    mix deps.get
    mix test
    MIX_ENV=prod mix escript.build
    ./{{ npm_name }} --column name --value alice < input.csv

Bad usage exits `2`, an unreadable file exits `1`.

## License

MIT — see [LICENSE](LICENSE).
