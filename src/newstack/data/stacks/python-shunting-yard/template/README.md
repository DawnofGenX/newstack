# {{ title }}

{{ description }}

to_postfix(expr) answers the postfix token list Dijkstra's yard
yields - output queued left to right, operators parked on a stack
that yields only to tighter binding. evaluate(tokens) walks a
postfix list and answers the single integer left standing.
value_of(expr) is both at once. The promise is checked, never
assumed: value_of(expr) equals the shipped recursive-descent
oracle on every shipped and seeded ledger, and evaluate of
to_postfix equals value_of, record after record.

## Why

An evaluator earns trust the only way an evaluator can: its
answer must equal an independent parse of the same grammar, on
every expression - and the queue it yields must reckon to that
same answer. So this tool exists to *show* that, not to state it:

```sh
$ {{ npm_name }} eval "3 + 4 * 2 / ( 1 - 5 ) * 2"
```

Every claim below is a comparison the selftest computes at run
time against the real modules, and `selftest` refuses to pass when
one stops holding. The falsifiable core is the pair: `oracle.py`
parses and answers by descending the grammar - sum over product
over atom - never by shunting, and every answer the yard gives the
oracle gives too.

## The rules

| rule | what it forbids | where it is proved |
| ---- | --------------- | ------------------ |
| the pair answers alike | a yard the oracle contradicts | value_of equals descent on shipped and seeded ledgers |
| the queue reckons | a queue that means another sum | evaluate(to_postfix(expr)) is value_of(expr) |
| the operator stack yields only to tighter binding | a pop that eats a tighter park | `* /` outrank `+ -` on every yielded queue |
| every operator binds left | a sum that re-groups itself | 100 - 20 - 5 is 75, 100 / 5 / 2 is 10 |
| a division floors | a fraction wearing an integer coat | 6 / 4 is 1, documented floor semantics |
| loud edges raise | a half expression that guesses | unbalanced parens and / 0 name the break |
| a forged ledger is named | an answer nobody recomputed | audit recomputes yard, oracle, reckoning |

## Quick start

```sh
cd your-project
uv sync
uv run {{ npm_name }} eval "3 + 4 * 2 / ( 1 - 5 ) * 2"
uv run {{ npm_name }} postfix "2 + 3 * 4"
uv run {{ npm_name }} report --corpus fixtures/records.txt
PY=.venv/bin/python bash smoke.sh
```

## Commands

| command | question it answers |
| ------- | ------------------- |
| `eval EXPR` | the value, oracle-checked before it prints |
| `postfix EXPR` | the queue the yard yields |
| `report --corpus FILE` | a ledger, audited record after record |
| `demo` | six stories about the yard, with real numbers |
| `selftest` | the invariants, runnable in a fresh checkout |

## Input format

Expressions are nonneg integers, `+ - * /`, and parentheses over
at most 10,000 characters: no floats, no letters, no leading
zeros, no power, no modulo. `/` is floor division - `6 / 4` is
`1` - and a division by zero raises. `fixtures/records.txt` is one
record per line, `infix | postfix | value`; blank lines and lines
starting with `#` are skipped, and every other line must audit
silent. A postfix queue is the space-separated character face:
`2 3 4 * +` is the queue `1 + 2 * 3` yields.

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | an answer was given, or the invariants hold |
| 1 | the oracle answered elsewhere, a story fails |
| 2 | the input cannot be read: a loud expression, a bad file |

## Files

```
src/{{ package_name }}/expr.py           the gate: tokens, precedence, ceiling
src/{{ package_name }}/yard.py           the shunting yard: to_postfix
src/{{ package_name }}/calc.py           the reckoning: evaluate, value_of
src/{{ package_name }}/oracle.py         the recursive descent, another way
src/{{ package_name }}/corpus.py         ledgers in, audits out
src/{{ package_name }}/demo.py           six stories, every claim computed
src/{{ package_name }}/cli.py            the command line
src/{{ package_name }}/selftest.py       the invariants, runnable in a checkout
fixtures/records.txt                     a ledger the smoke test builds on
smoke.sh                                 the tool driven the way a user drives it
```

## Non-goals

No floats, no powers, no modulo, no unary minus, no variables, no
letters, no arbitrary precision, no language but integer
arithmetic. The yard is the documented shunting yard it is: a
tool for showing what a stack promises an answer, not a replacement
for a calculator.
