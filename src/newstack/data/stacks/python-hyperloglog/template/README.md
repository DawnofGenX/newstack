# {{ title }}

{{ description }}

Counting distinct values exactly means holding every value. A sketch holds a fixed number of
registers instead, and the only honest way to ship that trade is to print the error beside the
number. This one estimates cardinality with HyperLogLog: the estimate carries a promised standard
error of `1.04 / sqrt(m)`, the demo measures that promise at four scales and five precisions, and
the two corrections that keep small and huge cardinalities honest are exercised rather than
assumed.

## The rules this code keeps

1. **The error is printed beside the number.** `estimate` prints the estimate and the promised
   error; `estimate --expect N` exits 1 when the measured error is outside four standard errors,
   so the promise is a gate and not a footnote.
2. **The register index and the rank are independent.** The index comes from the top `p` bits of
   a 64-bit blake2b hash and the rank from the bits that remain. Reading the index from the low
   bits of a hash that keeps structure there puts correlated items in one register, and story 5
   shows the estimate collapsing when that happens.
3. **Hash values are stable across processes.** `hash()` is salted per interpreter, so sketches
   built by two processes could never be merged. blake2b is the same everywhere, which is what
   makes `merge` meaningful.
4. **Union is a register-wise maximum, never a sum.** Two halves merged in story 3 produce
   byte-identical registers to one pass over the whole input; the story also prints the sum of the
   two estimates so the wrong answer is visible next to the right one.
5. **Small and huge cardinalities use different estimators.** Below `2.5 * m` registers with a
   zero remaining, linear counting (`m * ln(m / zeros)`) replaces the biased harmonic estimate;
   above `2**64 / 30` a logarithm replaces arithmetic that has run out of float precision.
6. **A merge that would reinterpret registers is refused.** Different precisions mean different
   indexes, so `merge` exits 2 with an explanation instead of averaging two incompatible sketches.
7. **Duplicates cost time, not accuracy.** Registers only grow, so re-adding 10,000 items 90,000
   times changes nothing; the add counter and the distinct estimate are reported separately.

## What the demo prints

```
1. an estimate beside the memory it saved
  exact set            10000 distinct, about 999.4 KiB
  sketch                9978 distinct, 16.0 KiB (precision 14)
  error            -0.22%, promised 0.81%
  registers raised      8246 of 10000 adds
  -> holds

2. the error stays inside the promise for every scale
    distinct  estimate     error  promised  within
        100        100    +0.00%   1.62%  yes
       1000        997    -0.30%   1.62%  yes
      10000       9859    -1.41%   1.62%  yes
     100000      98698    -1.30%   1.62%  yes
  -> holds

3. merging two halves equals one pass over the whole
  left                  2470 from 2500 adds
  right                 2500 from 2500 adds
  merged                4914
  direct                4914
  registers equal  yes
  estimates added       4970 (wrong: union is max, not sum)
  -> holds

4. duplicates do not move the estimate
  after 10,000 adds      9859
  after 100,000          9859
  registers changed         0
  adds counted         100000 (separate from distinct)
  -> holds

5. a hash without entropy in the bits you read collapses the sketch
  blake2b 64-bit        9760 for 10,000 distinct numbers
  low 32 bits only         1
  registers used           1 of 4096
  the biased hash keeps zeroes in its low bits, so a low-bit index
  sends every item to register 0 and the rank is all that is left
  -> holds

6. precision buys accuracy and pays in registers
  precision  registers  memory   promised  measured
          8        256  0.2 KiB     6.50%    -7.35%
         10       1024  1.0 KiB     3.25%    -1.90%
         12       4096  4.0 KiB     1.62%    -1.30%
         14      16384  16.0 KiB     0.81%    +0.03%
         16      65536  64.0 KiB     0.41%    +0.27%
  -> holds
```

## Use it

```console
$ printf 'alice\nbob\nalice\n' | {{ npm_name }} build --sketch /tmp/seen.json
$ {{ npm_name }} estimate --sketch /tmp/seen.json --expect 2
$ {{ npm_name }} info --sketch /tmp/seen.json
```

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | the command answered |
| 1 | the estimate missed the count it was told to expect (`estimate --expect`) |
| 2 | the command could not run: unreadable sketch, corrupt JSON, incompatible merge |

## What this stack does not do

* No sparse representation. A sparse sketch matters at very low cardinalities, where 16 KiB of
  zero registers is mostly waste; the estimator here handles that case with linear counting.
* No bias correction tables. The published corrections improve accuracy at the low end; the
  promise printed here is the uncorrected standard error, which the measurements stay inside.
* No persistence beyond one JSON file, and no partial-merge protocol across hosts.
