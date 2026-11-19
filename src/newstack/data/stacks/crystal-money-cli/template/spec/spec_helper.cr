require "spec"

# Require the modules, not `../src/money.cr`: the facade calls `exit` at the top
# level, which a spec process must not do.
require "../src/money/amount"
require "../src/money/cli"
