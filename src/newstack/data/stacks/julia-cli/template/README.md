# {{ title }}

{{ description }}

A Julia command line tool that counts lines, words and bytes the way `wc`
does. Counting lives in a pure function (`Textstat.counts`), argv parsing in
another pure function (`Textstat.parse_args`), and `bin/textstat.jl` is the only
file that reads a device, prints, or exits — so the test suite drives the logic
directly and checks exit codes by running the real script.

No dependencies: the `Test` standard library is the whole test framework, and
`Project.toml` has an empty `[deps]` section.

## Layout

```
Project.toml                     package metadata, empty [deps]
src/Textstat.jl                  module; includes the two files below
src/counts.jl                    Counts value type and pure counts(data)
src/options.jl                   Options type, parse_args, usage text
bin/textstat.jl                  entry script: argv, output, exit code
test/runtests.jl                 Test stdlib suite: counting, parsing, exit codes
```

`exit` is called once, at the bottom of `bin/textstat.jl`. Nothing under `src/`
prints or exits, so tests never have to trap a process exiting underneath them.

## The package name and UUID are fixed

Julia requires the `name` in `Project.toml` and the module name to be
identifiers, so this template always ships `name = "Textstat"` and
`module Textstat`, whatever the project directory is called. To rename it:

1. Change `name` in `Project.toml`.
2. Rename `src/Textstat.jl` and change the `module Textstat` line.
3. Change `using Textstat` in `bin/textstat.jl`, and the `Textstat.` prefixes it
   uses for `Counts`, `counts`, `parse_args`, `usage` and `version`.
4. Update this README.

`Project.toml` also carries a literal `uuid`, because Julia requires one for a
package. It is the identity of *this template*, not of your project: before
publishing a package, generate your own with

```console
$ julia -e 'using UUIDs; println(uuid4())'
```

and paste it into `Project.toml`. Never change the UUID of a package that has
already been registered or depended on — dependents key on it.

## Run

```console
$ julia --project=. -e 'using Pkg; Pkg.instantiate(); Pkg.precompile()'
$ julia --project=. bin/textstat.jl --help
$ julia --project=. bin/textstat.jl README.md
$ printf 'one two\nthree\n' | julia --project=. bin/textstat.jl -w
```

`-l`, `-w` and `-c` select lines, words or bytes; with no flag all three are
printed, and more than one file gets a `total` row. Bad usage exits `2`, an
unreadable file exits `1`, everything else exits `0`.

The first run after a change pays Julia's JIT and precompilation cost; later
runs of the same code start in well under a second.

## Test

```console
$ julia --project=. test/runtests.jl
```

The suite covers empty input, trailing and missing final newlines, runs of
whitespace, multi-byte UTF-8 (bytes, not characters), every branch of the
option parser, and the three exit codes — the last through
`run(pipeline(...))` on the real script, not a stubbed `exit`.

## License

MIT — see [LICENSE](LICENSE).
