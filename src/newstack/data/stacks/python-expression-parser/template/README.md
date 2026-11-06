# {{ title }}

An arithmetic expression parser and evaluator that tells you exactly what it
did, and refuses to guess when it cannot be exact.

```
$ {{ npm_name }} eval "2 + 3 * 4"
render     2 + 3 * 4
value      14
mode       exact
```

The point of the project is not that it adds numbers. It is that the three
things a small calculator usually gets wrong — precedence, printing, and
exactness — are each handled in a way you can check.

## What it refuses to do

Seven rules, each with a test that fails if it is broken:

1. **Precedence is a table, not the order of an `if` ladder.** `2 + 3 * 4`
   is 14 and `(2 + 3) * 4` is 20; the parser prints both trees.
2. **`^` is right-associative.** `2 ^ 3 ^ 2` is 512, not 64.
3. **A power binds tighter than the minus in front of it.** `-2 ^ 2` is -4,
   while `(-2) ^ 2` is 4. A negative exponent is still allowed: `2 ^ -1` is 0.5.
4. **Printing a tree and reading it back gives the same tree.** The printer
   adds a parenthesis only where removing it would change the parse:
   `2 * (3 + 4)` keeps its pair, `(2 * 3) + 4` loses one.
5. **Exact mode refuses an answer it cannot write down.** `0.1 + 0.2` is
   `0.3` and `1 / 8` is `0.125`, but `1 / 3` is refused by name — the tool
   will not print `0.3333333` and call it the answer. Ask for `--inexact` and
   it rounds at 28 significant digits, half-even, and says so.
6. **Every error names the column it is about.** Not "syntax error" but
   `expected a number, a name or '(' here, found '*' at column 5`, with a
   caret under the offending character.
7. **A chained comparison is refused, not silently left-associative.**
   `1 < 2 < 3` in Python means `(1 < 2) and (2 < 3)`; here it is an error,
   because the two readings disagree and the tool cannot know which you meant.

## Install

```
cd your-project
uv sync
```

## Use

```
$ {{ npm_name }} eval "2 ^ 3 ^ 2"
render     2 ^ 3 ^ 2
value      512
mode       exact

$ {{ npm_name }} eval "-2 ^ 2"
render     -2 ^ 2
value      -4
mode       exact

$ {{ npm_name }} eval "1 / 3"
{{ npm_name }}: 1 / 3 is 1/3, which has no finite decimal expansion; pass --inexact to round it to 28 digits at column 3
  1 / 3
    ^

$ {{ npm_name }} eval "1 / 3" --inexact
render     1 / 3
value      0.3333333333333333333333333333
mode       rounded to 28 digits
```

`parse` shows the tree, `explain` shows the precedence table and the value:

```
$ {{ npm_name }} parse "2 * (3 + 4)"
source     2 * (3 + 4)
render     2 * (3 + 4)
depth      3
nodes      5
tree
  *   multiplicative, column 3
    2   atom
    +   additive, column 8
      3   atom
      4   atom

$ {{ npm_name }} explain "2 + 3 * 4"
source     2 + 3 * 4
render     2 + 3 * 4
precedence (lower binds looser)
  1  !=
  1  <
  1  <=
  1  ==
  1  >
  1  >=
  2  +
  2  -
  3  %
  3  *
  3  /
  4  unary + -
  5  ^
tree
  +   additive, column 3
    2   atom
    *   multiplicative, column 7
      3   atom
      4   atom
value      14
```

Variables are passed with repeated `--var name=value`; a name that was never
given a value is an error, not a zero:

```
$ {{ npm_name }} eval "x * 2" --var x=21
render     x * 2
value      42
mode       exact
```

`parse --json` emits the same tree as data:

```
$ {{ npm_name }} parse "2 * 3" --json
{
  "source": "2 * 3",
  "render": "2 * 3",
  "depth": 2,
  "nodes": 3,
  "tree": {
    "kind": "binary",
    "op": "*",
    "left": {
      "kind": "number",
      "value": "2"
    },
    "right": {
      "kind": "number",
      "value": "3"
    }
  }
}
```

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | the expression was parsed (and, for `eval`/`explain`, valued) |
| 1 | the expression is well formed but has no exact value, or names a value that was not given |
| 2 | the command or the expression could not be understood |

## Languages of the values

Numbers are `Decimal`s in exact mode and `Fraction`s underneath, so
`0.1 + 0.2` is exactly `0.3` rather than `0.30000000000000004`. Nothing here
touches a `float` on the way to an answer.

## The grammar

```
expression  -> comparison
comparison  -> additive ( ("<" | ">" | "<=" | ">=" | "==" | "!=") additive )?
additive    -> multiplicative ( ("+" | "-") multiplicative )*
multiplicative -> unary ( ("*" | "/" | "%") unary )*
unary       -> ("+" | "-") unary | power
power       -> primary ( "^" unary )?
primary     -> NUMBER | NAME | NAME "(" args ")" | "(" expression ")"
args        -> expression ( "," expression )+
```

A call with no arguments — `f()` — is refused: a call with nothing in it is
not a call in this language.

## Files

```
src/{{ package_name }}/lexer.py      tokens, and the column each one starts at
src/{{ package_name }}/nodes.py      the tree, its precedence, and its printer
src/{{ package_name }}/parser.py     precedence climbing
src/{{ package_name }}/evaluator.py  exact arithmetic that refuses to round
src/{{ package_name }}/demo.py       six stories, each with its own check
src/{{ package_name }}/cli.py        parse / eval / explain / demo / selftest
fixtures/expressions.txt             eighteen expressions and their values
smoke.sh                             end-to-end checks against the command
```

## Verify

```
uv run pytest -q
{{ npm_name }} selftest
PY=.venv/bin/python bash smoke.sh
```

`selftest` is 88 checks over the same ground as the tests but reached through
the public command; it prints `selftest: 88 checks passed, 0 failed`.

## Non-goals

Not a calculator for money (see `python-money-allocation`), not an
interpreter — there is no assignment, no statement, no variable scope beyond
`--var`, and no functions other than the five in `FUNCTIONS`. It does not
parse Python or any other language; it parses this one, and it is small enough
to read in an afternoon.

## License

MIT.
