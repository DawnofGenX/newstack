# {{ title }}

{{ description }}

A two-proportion test is four lines of arithmetic. Everything that goes wrong
with an A/B test happens around those four lines: somebody looks at the
dashboard every morning, the assignment breaks and one arm gets more traffic,
or a test that could never have seen the effect is reported as "no effect".
This project computes the arithmetic and then MEASURES the three failure modes
instead of warning about them.

## The rules this project keeps

1. **The p-value belongs to a horizon that was fixed in advance.** `compare`
   is one look. Reading it every day is a different test with a different error
   rate, and the demo measures both on the same simulated worlds.
2. **Every rate carries a Wilson interval, the difference carries its own
   interval, and the lift carries the same interval divided by the baseline.**
   A bare percentage with no interval hides how little a small sample says.
3. **The test uses the pooled error, the interval uses the unpooled one.** Under
   the null both arms share one rate; under the alternative they do not. Using
   one number for both jobs is how intervals and p-values start disagreeing.
4. **A sample-ratio mismatch is checked before the lift is read.** If traffic
   arrived 50.5/49.5 when the assignment promised 50/50, the lift measures the
   assignment, not the product. The gate exits 1 on its own.
5. **Peeking is simulated, not asserted.** The demo runs the same worlds through
   one look, a flat line at every look, and an O'Brien-Fleming spending
   boundary, so the inflation and the repair are both numbers.
6. **The spending boundary is a schedule, not a promise.** Its thresholds treat
   the looks as independent, so it lands near the label rather than exactly on
   it; the demo prints the leftover instead of hiding it.
7. **"Not significant" is not "no effect".** `compare` prints the interval that
   says what the data still cannot rule out, and `power` prints the sample a
   real effect would have needed.

## Try it

```console
$ {{ npm_name }} compare --control control=100/1000 --treatment treatment=130/1000
control      control        100 of 1000    = 10.00%  wilson [+0.0829, +0.1202]
treatment    treatment      130 of 1000    = 13.00%  wilson [+0.1106, +0.1523]
difference   +0.0300 (+30.00% relative), 5% interval [+0.0021, +0.0579]
z            +2.1027    two-sided p 0.0355
verdict      higher
note         a p-value is only a fixed-horizon claim; see `peeking`
```

```console
$ {{ npm_name }} srm --control control=500/102000 --treatment treatment=500/100000
split        0.5050 against an expected 0.5000
chi-square   19.802 on one degree of freedom
p-value      8.589e-06
verdict      MISMATCH at alpha 0.001
$ echo $?
1
```

```console
$ {{ npm_name }} power --baseline 0.10 --lift 0.05 --visitors 20000
baseline     10.00%
lift         +5.0% relative, so 10.5000%
alpha        0.05   power 0.8
per arm      57,763 visitors
both arms    115,526 visitors
at 20,000   only a 8.56% relative lift would be caught
```

```console
$ {{ npm_name }} peeking --trials 300 --visitors 2000 --looks 5 --seed 5
worlds       300 trials, both arms truly 10.00%, 2000 visitors each
one look        14 of 300 =  4.67% crossings
every look      43 of 300 = 14.33% crossings with a flat 5% line
boundary        18 of 300 =  6.00% crossings with the spending boundary
critical     first look |z| 4.383, last look |z| 1.960
verdict      the boundary held at 6.00%; the flat line spent 14.33%
```

`demo` prints six stories and ends each with `-> holds` or `-> BROKEN`, and
exits 1 if any story broke. A real run, abridged:

```text
2. every look is another chance to cross the line
  worlds       1000 trials, both arms truly 10.00%, 2000 visitors each
  one look        45 of 1000 =  4.50% crossings
  every look     189 of 1000 = 18.90% crossings with a flat 5% line
  boundary        67 of 1000 =  6.70% crossings with the spending boundary
  inflation    4.2x the false-positive rate on the same worlds
  nothing about the traffic changed; only the number of decisions did
  -> holds

3. a spending boundary buys most of the peeking back
  flat line    18.90% of worlds cross a 5% line at some look
  boundary      6.70% of the same worlds cross the boundary
  second world  7.20% at a 20% baseline, against 20.50% for the flat line
  first look   |z| must reach 6.20, not 1.96
  left over    +1.70% against the label: the thresholds treat the looks as independent, and this simulation is the honest correction
  the cost is time, not truth: an effect is declared later, and never falsely sooner
  -> holds
```

The other four stories: a fixed-horizon test answering one question, a 1%
traffic imbalance voiding a lift that looks plausible at a fifth of a percent,
the sample size as a decision (57,763 per arm for a 5% lift on 10%), and a
three-point lift on a hundred visitors that is indistinguishable in both
directions.

## Commands

| command | what it answers |
| --- | --- |
| `compare --control A --treatment B [--alpha --json]` | is the difference bigger than its error, and how big could it still be |
| `srm --control A --treatment B [--alpha --json]` | did traffic arrive in the promised split (exit 1 on a mismatch) |
| `power --baseline P --lift L [--visitors N]` | how many visitors an effect needs, and what a sample could catch |
| `peeking [--trials --visitors --looks --seed --alpha --json]` | what looking every day costs, measured on simulated worlds |
| `demo` | the six stories, each with a verdict |
| `selftest` | the same rules as in-process checks |

Arms are written `name=conversions/visitors`, e.g. `control=100/1000`.
`--json` prints the same numbers as an object for a pipeline to read.

## Exit codes

| code | meaning |
| --- | --- |
| 0 | the question was answered, and any gate that applies was passed |
| 1 | a gate failed: an SRM mismatch, a boundary that did not hold, or a demo story that broke |
| 2 | the input cannot support an answer (a malformed arm, a probability outside 0..1, a boundary with no looks) |

## Layout

```text
src/{{ package_name }}/stats.py       proportions, Wilson, the pooled test, sample size
src/{{ package_name }}/srm.py         the sample-ratio-mismatch gate
src/{{ package_name }}/sequential.py  the spending boundary and the peeking simulation
src/{{ package_name }}/rng.py         a SplitMix64 generator, so a published curve is reproducible
src/{{ package_name }}/demo.py        the six stories
src/{{ package_name }}/cli.py         the command line
src/{{ package_name }}/selftest.py    the rules as in-process checks
tests/                                the same rules again, as pytest cases
smoke.sh                              every claim above, once, against the built project
```

## What this project does not do

- It does not decide what your metric means, or whether the assignment was
  random in the first place. `srm` checks the split, not the randomisation
  mechanism.
- It does not do sequential tests with a fully calibrated error rate: the
  O'Brien-Fleming boundary here is the textbook schedule, and the demo's job is
  to show how close it lands rather than to promise alpha exactly.
- It does not do CUPED, stratification, or any variance reduction. Fewer
  visitors per effect is a different project.
- The generator is not cryptographic. It exists so that a story you paste into
  a review reproduces on somebody else's machine.

Run `{{ npm_name }} selftest` for the rules as checks, and `bash smoke.sh` for
the same claims against the built command.
