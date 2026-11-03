require "spec"

# Require the modules, not `../src/textstat.cr`: the facade is the binary's
# entry point and calls `exit` at the top level, which a spec process must not
# do. The CLI spec compiles the facade separately and checks the real exits.
require "../src/textstat/cli"
