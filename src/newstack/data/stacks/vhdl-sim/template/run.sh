#!/usr/bin/env sh
# Analyze, elaborate and run the testbench.  GHDL is not a build system: this
# script is, and it is the same three commands on every machine.
set -eu
std=${GHDL_STD:-08}
root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$root"

ghdl --clean >/dev/null 2>&1 || true
ghdl -a --std="$std" rtl/*.vhd tb/*.vhd
ghdl -e --std="$std" counter_tb
ghdl -r --std="$std" counter_tb --assert-level=error --stop-time=10us
