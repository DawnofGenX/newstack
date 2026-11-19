require "./hex/dump"
require "./hex/options"
require "./hex/cli"

exit Hex::CLI.run(ARGV, STDOUT, STDERR, STDIN)