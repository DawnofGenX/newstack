"""
    CsvKit

CSV parsing and reporting for the command line.

`parse_csv` is pure, `parse_args` never prints or exits, and only
`bin/{{ npm_name }}.jl` touches a device or an exit code.
"""
module CsvKit

include("csv.jl")
include("options.jl")

export CsvError, CsvTable, parse_csv, render_csv, column_index, select_columns,
       column_summary, to_json, Options, parse_args, usage, version

end
