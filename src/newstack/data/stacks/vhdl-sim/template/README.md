# {{ npm_name }}

An 8-bit up/down counter and a self-checking testbench, simulated with GHDL.
It is the newstack `vhdl-sim` starter: a synthesizable design, a testbench that
fails the simulation instead of printing numbers for a human to read, and a
script that runs the three GHDL commands in the right order.

## What is here

    rtl/counter.vhd     the design: one clocked process, synchronous load,
                        up/down, and a carry level
    tb/counter_tb.vhd   a self-checking testbench (asserts, no eyeballing)
    run.sh              analyze, elaborate, run — and exit non-zero on any
                        failed assertion
    .gitignore          GHDL's work library and wave dumps

## Getting started

    ./run.sh

That prints `PASS: counter testbench complete` and exits 0 when the design is
correct.  When it is not, the first failed assertion ends the run with the
message, the expected value and the actual value:

    tb/counter_tb.vhd:40:5:@46ns:(assertion error): three counts up: got 2, want 3
    ghdl:error: assertion failed

## Why the assertions matter more than the waveforms

A testbench that only dumps a VCD is a testbench nobody runs in CI.  Every
check here is an `assert` with `severity error`, and `run.sh` passes
`--assert-level=error`, so a wrong design turns into a non-zero exit code.  The
`inject_fault` generic is the proof that the asserts are wired up: the shipped
workflow runs the testbench a second time with it enabled and requires that run
to fail.  If it ever passes, the checks have stopped testing anything.

## Reading the design

`rtl/counter.vhd` is deliberately dull: one `rising_edge(clk)` process, one
branch per behaviour (reset, load, enable+up, enable+down), and a carry that is
a level rather than a pulse so a downstream stage can sample it on the same
edge.  There is no state machine to learn before you can change it.

## GHDL on your machine

`ghdl -a` analyzes, `ghdl -e` elaborates, `ghdl -r` runs.  `run.sh` also calls
`ghdl --clean` first so a stale `work-obj08.cf` cannot hide a change.  Pass
`GHDL_STD=93` (or `--std=` yourself) if you need the older standard.

## Licence

MIT, see `LICENSE`.
