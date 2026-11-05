# {{ title }}

Feature flags that can answer the only question support ever asks: *why is it off
for this user?* Every decision carries its arithmetic — the bucket, the cutoff,
the rule that won — and the bucket does not move when the process restarts.

No dependencies, no service, no SDK: `tomllib` and `hashlib` from the standard
library, one TOML file, and a CLI you can paste into a ticket.

## Quick start

```console
$ uv venv && uv pip install -e . pytest ruff
$ python -m {{ package_name }} list
checkout-redesign        on   10%  salt=checkout-2026-11
new-search               on   50%  salt=search-2026-11
dark-mode                on  100%  salt=dark-2026-01
kill-switch-test         off 100%  salt=kill-2026-11
vip-access               on    0%  salt=vip-2026-11 targets=2
```

The question, answered with the reason and the numbers behind it:

```console
$ python -m {{ package_name }} explain checkout-redesign --user alice
flag     checkout-redesign
user     alice
salt     checkout-2026-11
bucket   1717 of 10000 (17.17%)
cutoff   1000 (rollout 10%)
enabled  true
targets  -
decision off (outside)
```

`check` is the same decision without the prose, and it is usable as a gate: exit
`0` when the user is on, `1` when the user is off, `2` when the flag file or the
arguments are wrong.

```console
$ python -m {{ package_name }} check dark-mode --user alice; echo $?
on  inside    dark-mode                bucket 6036 < 10000
0
$ python -m {{ package_name }} check vip-access --user alice; echo $?
on  targeted  vip-access               bucket 9449 <    0
0
$ python -m {{ package_name }} check no-such-flag --user bob; echo $?
off unknown   no-such-flag             bucket    0 <    0
1
```

`--json` gives the same answer as data, for the ticket or the dashboard:

```console
$ python -m {{ package_name }} check new-search --user alice --json
{
  "flag": "new-search",
  "user": "alice",
  "variant": "off",
  "reason": "outside",
  "bucket": 8042,
  "cutoff": 5000,
  "rollout": 50
}
```

And because "10%" is a claim, `distribution` measures it against a population:

```console
$ python -m {{ package_name }} distribution --users 10000
flag                      wanted  measured  off by
checkout-redesign            10%    10.22%  +0.22%
new-search                   50%    49.91%  -0.09%
dark-mode                   100%    100.0%   +0.0%
kill-switch-test            100%    100.0%   +0.0%
vip-access                    0%      0.0%   +0.0%

worst deviation: checkout-redesign at +0.22 percentage points
```

The numbers are reproducible: the same salt and user always land in the same
bucket, on every process, on every machine, forever.

## Precedence

Four rules, checked in this order, and the first one that fires is the reason
the decision reports:

| rule | condition | reason |
| --- | --- | --- |
| unknown | the flag is not in the file | `unknown` |
| kill switch | `enabled = false` | `off` |
| targeting | the user is listed in `targets` | `targeted` |
| rollout | `bucket_of(salt, user) < rollout * 100` | `inside` / `outside` |

A kill switch beats targeting on purpose: the reason you flip `enabled = false`
is that you want it off for the person you also targeted.

## Exit codes

| code | meaning |
| --- | --- |
| 0 | the flag is on for this user, or the command succeeded |
| 1 | the flag is off for this user, or `distribution`/verification failed |
| 2 | the flags file or the arguments are unusable |

## Layout

| path | what it is |
| --- | --- |
| `src/<package>/model.py` | `Flag`, `FlagSet`, and the validation that runs before anything else |
| `src/<package>/bucket.py` | the bucket function, and why it is SHA-256 |
| `src/<package>/config.py` | TOML loading, with every bad flag reported at once |
| `src/<package>/evaluate.py` | the precedence table, and `explain` |
| `src/<package>/cli.py` | `list`, `check`, `explain`, `distribution`, `selftest` |
| `fixtures/flags.toml` | five flags covering rollout, targeting, and a kill switch |
| `smoke.sh` | 21 checks against the built package |

## Traps this stack exists to demonstrate

1. **`hash()` is randomised per process.** Python salts string hashing with
   `PYTHONHASHSEED`, so `hash(user) % 100` gives a different rollout on every
   start — users flip on and off on every deploy, and no test using one process
   can see it. `bucket_of` uses SHA-256 over `salt:user`, and the test suite runs
   the same script under two `PYTHONHASHSEED` values to prove one answer.
2. **0% must admit nobody.** `bucket < rollout * 100` with a strict `<` means a
   0% rollout has cutoff 0 and no bucket is below it, while 100% has cutoff
   10000 and every bucket is. `<=` would leak one user in a thousand at 0%.
3. **A salt per flag, not per system.** Sharing one salt puts the same users in
   every experiment, so the 10% who see the new checkout are exactly the 10% who
   see the new search — and you cannot tell the two effects apart.
4. **Percentages are integers, and the cutoff is in basis points.** A flag has a
   percent and a cutoff derived from it, never a float: `0.1 * 10000` is
   `1000.0000000000001`-adjacent territory, and the boundary case is the one
   that decides who sees the feature.
5. **"on" is not "inside".** A targeted user is on at 0% rollout, and a
   kill-switched flag is off at 100%. The decision carries the variant *and* the
   reason, because they answer different questions.
6. **An unknown flag is a reason, not a crash.** Typo'd flag names are common
   (they come from tickets); `unknown` is reported like any other rule, and the
   CLI exits 1 rather than raising.
7. **A missing salt is refused.** Without one, every rollout is a different
   experiment with the same name. The constructor says so instead of hashing an
   empty string.
8. **Every bad flag is reported at once.** Configuration files are edited by
   humans; stopping at the first typo turns one edit into six deploys.

## Why a pros/cons table is not enough

The file format is deliberately boring — `[[flag]]` arrays in TOML, no remote
API, no evaluation server. The interesting part is that the arithmetic is in the
decision: if you can print the bucket and the cutoff, you can settle an argument
about a rollout without a debugger. When you outgrow this, the shape to keep is
`decide(flags, name, user) -> Decision`; wire it to whatever store you like.
