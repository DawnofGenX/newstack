"""
    Textstat

Line, word and byte counting for the command line.

`counts` is pure, `parse_args` never prints or exits, and only
`bin/textstat.jl` touches a device or an exit code.
"""
module Textstat

include("counts.jl")
include("options.jl")

export Counts, counts, Options, parse_args, usage, version

end
