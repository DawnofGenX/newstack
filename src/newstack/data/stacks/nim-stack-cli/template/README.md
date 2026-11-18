# {{ title }}

{{ description }}

A stack machine is the smallest interesting interpreter: numbers push, words
combine, and everything else is error handling. This one keeps the whole machine
in `src/{{ package_name }}/vm.nim` as a plain object with no globals, so the tests
drive it directly instead of spawning a process.

## Layout

```
src/{{ package_name }}/vm.nim        Vm: the stack, step(), eval(), VmError
src/{{ package_name }}/options.nim   argv parsing: Options with a Status
src/{{ package_name }}.nim           entry point: stdin, stdout, exit codes
tests/test_all.nim                   vm, options and real-binary exit codes
```

## Usage

```console
$ nimble build
$ ./{{ npm_name }} 2 3 +
5
$ ./{{ npm_name }} 1 2 swap
2 1
$ ./{{ npm_name }} 7 2 /
3
$ printf '4 5 *\n' | ./{{ npm_name }}
20
$ ./{{ npm_name }} 1 2 frobnicate
error: not a number or command: 'frobnicate'
1 2
```

The stack is printed bottom-first on one line, so a partial program still shows
you what it had before it failed.

## Words

| word | effect |
| ---- | ------ |
| `+` `-` `*` `/` `%` | pop two, push one; integer division and remainder |
| `dup` | push a copy of the top value |
| `swap` | exchange the top two values |
| `drop` | discard the top value |
| `depth` | push the current depth |
| `abs` `neg` | unary |
| `min` `max` | keep the smaller or larger of the pair |
| a number | push it, negatives included |

Underflow is an error, never a zero: `'+' needs two values, have 1` names both
the word and what it found.

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | success, including `--help` and `-V` |
| 1 | the program failed: unknown word, underflow, division by zero |
| 2 | usage error: unknown option, or no program on argv or stdin |

Negative numbers are values, not options — `-5` pushes minus five, while `-x` is
a usage error. After `--` every argument is a word.

## Test

```console
$ nimble test
$ bash smoke.sh
```
