# {{ title }}

{{ description }}

A regular expression is compiled to a Thompson NFA and then *simulated*: every
step carries the set of states that are still possible, so the cost is one pass
over the text no matter what the pattern looks like. The same pattern is also
determinised, and the two machines are compared by enumeration, so the claim
"these are the same language" is checked rather than assumed.

## Why

A backtracking matcher answers correctly and then dies on `(a*)*b`. On fourteen
`a`s and no `b` it takes 114688 steps to say no, because nothing remembers that
it has already been in this position with this input. The set-based simulation
says no in 15 sets, one per character plus the start:

```
$ {{ npm_name }} compare '(a*)*b' aaaaaaaaaaaaaa
pattern    (a*)*b
text       'aaaaaaaaaaaaaa'
simulation 15 set(s) for 8 state(s)
backtrack  114688 step(s) to say it did not match
verdict    both engines agree
```

That is the whole argument. The rest of the tool exists to make it visible
and to keep it honest.

## The seven rules

1. **A step carries a set, not a guess.** After `d` in `(cat|dog)s?` both
   alternatives are still alive, so the set holds both paths. Nothing is
   chosen, so nothing has to be undone.
2. **The star's exit is a silent edge.** `a*` leaves the loop through an
   epsilon transition, which is why `a*b` matches `aaab` without backtracking.
3. **Search is leftmost first, then longest.** `ab|abc` on `zabc` returns
   `abc`, not `ab`: the order of alternatives does not decide how much text is
   taken.
4. **The DFA is the same machine, asked earlier.** Subset construction answers
   every question in advance, so running it is one table lookup per character.
5. **Equality is checked by enumeration.** `agrees` runs both machines over
   every string up to a length you name and fails if any answer differs.
6. **A refusal carries a position.** Every parse error says where it stopped
   and prints a caret under that column.
7. **Counted repetition is not in this engine.** `a{3}` is refused with an
   instruction to write the copies; the language is small on purpose.

## Quick start

```sh
cd your-project
uv sync
uv run {{ npm_name }} demo
uv run {{ npm_name }} explain '(cat|dog)s?' dogs
uv run {{ npm_name }} agrees '(a|b)*abb' --alphabet ab --max-len 5
PY=.venv/bin/python bash smoke.sh
```

## Commands

`match PATTERN TEXT` — does the pattern match the whole text.

```
$ {{ npm_name }} match 'a*b' aaab
pattern    a*b
text       'aaab'
verdict    the whole text matches
machine    6 state(s), 7 edge(s)
```

`search PATTERN TEXT` — the leftmost, then longest, match anywhere.

```
$ {{ npm_name }} search 'a+' xaay
pattern    a+
text       'xaay'
match      [1, 3) 'aa'
```

`explain PATTERN TEXT` — the state set after every character.

```
$ {{ npm_name }} explain '(cat|dog)s?' dogs
pattern    (cat|dog)s?
text       'dogs'
steps      4 character(s), 18 state(s) in the machine

   at  seen        states                          accepting
    0  -           {0, 2, 8}                       no
    1  'd'         {9, 10}                         no
    2  'o'         {11, 12}                        no
    3  'g'         {1, 13, 14, 15, 16}             yes
    4  's'         {15, 17}                        yes
```

`why PATTERN TEXT` — the verdict first, then the trace that supports it.

```
$ {{ npm_name }} why '(a*)*b' aaaaaaaaaaaaaa
pattern    (a*)*b
text       'aaaaaaaaaaaaaa'
verdict    no match, because no accepting state survived
prefix     no prefix of this text is accepted
note       the last step was carrying 6 state(s) at once, which is the set a
           backtracking engine would have to try one by one
```

`machine PATTERN` — every state and its edges, silent ones included.

```
$ {{ npm_name }} machine 'a*b'
pattern    a*b
nfa        6 state(s), 7 edge(s), 5 of them silent
accept     state 5, with no way out: True
  state 0   eps->2, eps->1
  state 1   eps->4
  state 2   a->3
  state 3   eps->1, eps->2
  state 4   b->5
  state 5   (no way out)
```

`dfa PATTERN` — the determinised machine and its size.

```
$ {{ npm_name }} dfa '(a|b)*abb'
dfa        6 state(s), 18 transition(s), 1 accepting
symbols    'ab' plus 'A' for everything else
```

`agrees PATTERN [--alphabet CHARS] [--max-len N]` — enumerate both machines.

```
$ {{ npm_name }} agrees '(a|b)*abb' --alphabet ab --max-len 5
pattern    (a|b)*abb
alphabet   'ab' and no other character matters
checked    63 string(s) of length 0..5
verdict    the two machines agree
```

`compare PATTERN TEXT` — the simulation against a backtracker, with both
counts. Exits 1 only if the two ever disagree.

`demo` — six stories about the machines; `selftest` — the invariants.

## Input format

`fixtures/patterns.txt` is tab separated: `pattern`, `text`, and `yes` or `no`
for whether the pattern should match the whole text. Blank lines and lines
starting with `#` are skipped. The smoke test runs every row.

The pattern language is literals, `.`, character classes (`[a-c]`, `[^0-9]`),
the shorthands `\d \s \w` and the escapes `\n \t` plus any metacharacter,
grouping `()`, alternation `|`, and the three repeats `*`, `+`, `?`.

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | the answer is yes, or the two machines agree |
| 1 | the answer is no, or the two machines disagree |
| 2 | the input cannot be read: a bad pattern, a bad option, a bad file |

## Files

```
src/{{ package_name }}/syntax.py    the pattern language, parser and printer
src/{{ package_name }}/nfa.py       Thompson construction and the state sets
src/{{ package_name }}/dfa.py       subset construction and the enumeration
src/{{ package_name }}/match.py     whole-text match, search and describe
src/{{ package_name }}/backtrack.py a backtracker with a step budget, for the comparison
src/{{ package_name }}/explain.py   the trace and the verdict lines
src/{{ package_name }}/cli.py       the command line
src/{{ package_name }}/selftest.py  the invariants, runnable in a fresh checkout
fixtures/patterns.txt               a corpus the smoke test walks
smoke.sh                            the tool driven the way a user drives it
```

## Non-goals

No backreferences, no lookaround, no counted repetition, no lazy quantifiers,
no Unicode property classes. This is a tool for explaining how set-based
matching works and for measuring the cost of not backtracking, not a
replacement for `re`.
