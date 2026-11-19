# {{ title }}

{{ description }}

A small Elixir command line tool that counts word frequencies. Tokenising,
ranking and rendering live in pure modules (`WordCount.Options`,
`WordCount.Counter`) so ExUnit drives them directly, and `WordCount.CLI` is a
thin shell around argv, input, output and the exit code. `escript` turns it
into a single runnable binary with no runtime dependencies.

## Usage

    mix deps.get
    mix test
    MIX_ENV=prod mix escript.build
    ./{{ npm_name }} -n 5 README.md
    cat article.txt | ./{{ npm_name }} -i --min-length 4 --json

Options: `-n/--top`, `-m/--min-length`, `-i/--ignore-case`,
`-s/--stopwords FILE`, `--sort freq|alpha`, `--tsv`, `--json`, `-u/--unique`,
`-t/--total`, `--help`, `--version`. With no file argument the tool reads
standard input, and `-` is standard input in the middle of a file list.

Bad usage exits `2`, an unreadable file exits `1`.

## License

MIT — see [LICENSE](LICENSE).
