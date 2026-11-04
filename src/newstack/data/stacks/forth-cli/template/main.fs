\ The entry point: take the arguments gforth was given, run the CLI and turn
\ its status into the process exit status.

require lib/counts.fs
require lib/options.fs
require lib/runner.fs

args-from-command-line
run (bye)
