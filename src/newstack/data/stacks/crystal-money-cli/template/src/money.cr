#!/usr/bin/env crystal
#
# The runnable command. This is the only file that calls `exit`.
require "./money/amount"
require "./money/cli"

exit Money::Cli.run(ARGV)
