# Entry point: the only file that touches ARGV, the standard streams and
# `exit`. Everything else lives in `Textstat::*` so specs can call it directly.

require "./textstat/counts"
require "./textstat/options"
require "./textstat/cli"

exit Textstat::CLI.run(ARGV, STDOUT, STDERR)
