# Command line

The project is driven by `make`, which wraps `mdbook` and the link checker.

## Commands

| command | what it does |
| ------- | ------------ |
| `make build` | build the book into `book/` |
| `make check` | check links and the summary, without building |
| `make test` | run the suites in `tests/` |
| `make serve` | serve the book on `http://localhost:3000` and rebuild on save |
| `make clean` | remove `book/` |

## Requirements

`mdbook` 0.4 or newer must be on `PATH`. Nothing else is needed: the checker and
the tests are POSIX shell.
