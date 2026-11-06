# {{ title }}

{{ description }}

A version range is not a string match and not a regular expression. It is a
union of intervals, plus one extra rule: a prerelease has to be named before it
is allowed. This package parses the range dialects you actually see in
`package.json`, prints every arm as an interval, answers "does this version
satisfy it" with a reason per arm, and proves when two ranges cannot overlap.

## The rules this parser keeps

1. **A version is ordered fields, not a decimal number.** `1.10.0` is above
   `1.9.0`, `1.0.0-alpha` is below `1.0.0`, and build metadata is not part of
   precedence: `1.0.0+left == 1.0.0+right`.
2. **Every range is printed as intervals.** `^1.2.3` is `[1.2.3, 2.0.0)`,
   `1.2` is `[1.2.0, 1.3.0)`, `1.2 - 2.3.4` is `[1.2.0, 2.3.4]`. If you cannot
   read the interval, the answer is not trustworthy either.
3. **Caret is three rules wearing one hat.** `^1.2.3` keeps the major,
   `^0.2.3` keeps the minor, `^0.0.3` keeps the patch. A partial caret pins
   only the fields you wrote: `^0.0` is `[0.0.0, 0.1.0)`, `^0` is `[0.0.0, 1.0.0)`.
4. **A comparator on a partial version moves to the edge.** `>1.2` means
   `>=1.3.0`, `<=1.2` means `<1.3.0`, and `<1.2` means `<1.2.0`. The parser
   never quietly treats `1.2` as `1.2.0` when the operator says otherwise.
5. **A prerelease is opt-in, per core.** `^1.2.0` refuses `1.3.0-beta`, no
   matter how the interval reads. `>=1.3.0-beta <2` allows `1.3.0-beta.2` and
   still refuses `1.4.0-rc.1`, because only `1.3.0` was named.
6. **An intersection is computed, not guessed.** `^1.2.3 && >=1.4.0 <1.5.0` is
   `[1.4.0, 1.5.0)`, `^1.0 && ^2.0` is empty, and a contradiction such as
   `>=2.0.0 <1.0.0` parses into an arm that allows nothing instead of raising.

## See it

```
$ {{ npm_name }} demo
1. a version is ordered fields, not a decimal number
  as decimals  1.10.0 > 1.9.0, because 10 > 9
  as versions  1.2.0 < 1.9.0 < 1.10.0
  1.10.0 sorts above 1.9.0: yes
  prereleases  1.0.0-alpha < 1.0.0-alpha.1 < 1.0.0-beta < 1.0.0
  a prerelease sorts below its release: yes
  1.0.0+left == 1.0.0+right: True
  build metadata does not take part in precedence: yes
  -> holds

2. caret is three rules wearing one hat
  ^1.2.3   [1.2.3, 2.0.0)
  ^1.2.3 allows 1.9.9 and refuses 2.0.0: yes
  ^0.2.3   [0.2.3, 0.3.0)
  ^0.2.3 allows 0.2.9 and refuses 0.3.0: yes
  ^0.0.3   [0.0.3, 0.0.4)
  ^0.0.3 allows 0.0.3 and refuses 0.0.4: yes
  -> holds

3. a partial version is an interval, not a wildcard string
  1.2      [1.2.0, 1.3.0)
  1.2 allows 1.2.99 and refuses 1.3.0: yes
  1        [1.0.0, 2.0.0)
  1 allows 1.9.9 and refuses 2.0.0: yes
  >1.2     >=1.3.0
  >1.2 allows 1.3.0 and refuses 1.2.9: yes
  <=1.2    <1.3.0
  <=1.2 allows 1.2.99 and refuses 1.3.0: yes
  *        *
  a bare wildcard allows a release: yes
  -> holds

4. hyphen ranges and || arms are intervals you can read
  1.2 - 2.3.4   [1.2.0, 2.3.4]
  the hyphen start is the lowest 1.2 version: yes
  the hyphen end is inclusive here: yes
  ~1.4 || ^2.0  [1.4.0, 1.5.0) || [2.0.0, 3.0.0)
  either arm is enough: yes
  the gap between the arms is real: yes
  -> holds

5. a prerelease is opt-in, and only where it is named
  ^1.2.0        [1.2.0, 2.0.0)
  a caret range does not opt into prereleases: yes
  >=1.3.0-beta <2  [1.3.0-beta, 2.0.0) (prerelease of 1.3.0)
  a named prerelease is allowed: yes
  another core's prerelease is still refused: yes
  -> holds

6. two ranges meet in a place you can point at, or nowhere
  ^1.2.3 && >=1.4.0 <1.5.0  [1.4.0, 1.5.0)
  the overlap keeps the tighter bound: yes
  and it is exactly the tighter interval: yes
  ^1.0 && ^2.0              empty
  disjoint ranges have no overlap: yes
  why 1.5.0 fails ~1.4 || ^2.0:
  verdict    does not satisfy ~1.4 || ^2.0
  arm 1 [1.4.0, 1.5.0): the version equals the upper bound 1.5.0, which is excluded
  arm 2 [2.0.0, 3.0.0): the version is below the lower bound 2.0.0
  the refusal is explained arm by arm: yes
  -> holds

stories      6 of 6 hold
```

## Read a range

```
$ {{ npm_name }} parse "~1.4 || ^2.0"
range      ~1.4 || ^2.0
arms       2
  1. [1.4.0, 1.5.0)
  2. [2.0.0, 3.0.0)
```

## Ask whether a version fits

```
$ {{ npm_name }} satisfy 1.4.2 --range "~1.4 || ^2.0"
version    1.4.2
range      ~1.4 || ^2.0
verdict    satisfies ~1.4 || ^2.0 (arm 1)
           arm 1 [1.4.0, 1.5.0): the version is inside [1.4.0, 1.5.0)

$ {{ npm_name }} satisfy 1.5.0 --range "~1.4 || ^2.0"
version    1.5.0
range      ~1.4 || ^2.0
verdict    does not satisfy ~1.4 || ^2.0
           arm 1 [1.4.0, 1.5.0): the version equals the upper bound 1.5.0, which is excluded
           arm 2 [2.0.0, 3.0.0): the version is below the lower bound 2.0.0
```

Exit `0` when it satisfies, `1` when it does not, `2` when the version or the
range cannot be read at all. A misspelled range is never a quiet "no".

## Meet two ranges

```
$ {{ npm_name }} intersect "^1.2.3" ">=1.4.0 <1.5.0"
left       [1.2.3, 2.0.0)
right      [1.4.0, 1.5.0)
  1. [1.4.0, 1.5.0)
verdict    1 arm(s)

$ {{ npm_name }} intersect "^1.0" "^2.0"
left       [1.0.0, 2.0.0)
right      [2.0.0, 3.0.0)
verdict    empty: no version satisfies both
```

## Sort a file of versions

```
$ {{ npm_name }} sort --input fixtures/versions.txt
0.9.9
1.0.0-alpha
1.0.0
1.2.3-beta.2
1.2.3
1.2.10
1.9.0
1.10.0
1.10.0+build.5
2.0.0
```

The fixture is deliberately unsorted and mixes prereleases, a ten-patch
version, and a build suffix; the output is precedence order, with build
metadata ignored. A bad line names its line number and exits `2`.

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | the range matched, or the command finished |
| 1 | the version does not satisfy the range, or the intersection is empty |
| 2 | unusable input: a version, range, or file that cannot be read |

## Layout

| path | what it holds |
| ---- | ------------- |
| `src/{{ package_name }}/version.py` | the three fields, prerelease precedence, strict parsing |
| `src/{{ package_name }}/ranges.py` | interval parsing: caret, tilde, hyphen, wildcard and `\|\|` |
| `src/{{ package_name }}/explain.py` | the decision and one reason per arm |
| `src/{{ package_name }}/demo.py` | the six stories above |
| `src/{{ package_name }}/cli.py` | `parse`, `satisfy`, `intersect`, `sort`, `demo`, `selftest` |

## What this stack does not do

- It does not resolve dependencies or pick a version for you; it answers
  membership questions and leaves the choice to the resolver.
- It does not repair a version string. `v1.2.3`, `1.02.3`, and `1.2` are
  refused, each with the reason, because a guessed version is a wrong build.
- It does not implement the full npm grammar (no `-` prerelease shorthand on
  the right of a caret, no `!=`); the dialects it does implement are the ones
  printed as intervals.

## Quick start

```
cd your-project
uv venv --allow-existing .venv
uv pip install --python .venv/bin/python -e . pytest ruff
.venv/bin/python -m {{ package_name }} demo
.venv/bin/python -m pytest -q
PY=.venv/bin/python bash smoke.sh
```
