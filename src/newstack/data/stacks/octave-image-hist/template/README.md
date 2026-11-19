# {{ title }}

Compute histograms and distribution statistics for grayscale Netpbm (PGM)
images. Both the ASCII `P2` and binary `P5` formats are supported; the core
library never opens a file itself, so the CLI and the tests share one reader
injection point.

## Usage

```sh
./bin/{{ npm_name }} image.pgm
./bin/{{ npm_name }} --bins 16 image.pgm
./bin/{{ npm_name }} --csv image.pgm
./bin/{{ npm_name }} --json image.pgm
./bin/{{ npm_name }} --equalize image.pgm
octave --no-window-system --quiet tests/run_tests.m
```

The default text view prints image geometry, sample count, mean, minimum,
maximum, distinct values and Shannon entropy, then the three most populated
bins. `--csv` emits one `bin,count` line per bucket; `--json` prints a compact
summary object; `--equalize` maps each pixel through the normalised CDF.
Exit status is 0 on success, 1 on a read/parse error, 2 on a usage error.
