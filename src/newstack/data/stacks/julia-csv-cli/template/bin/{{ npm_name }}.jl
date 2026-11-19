#!/usr/bin/env julia
#
# The runnable command: argv in, rows out, an exit code back. This is the only
# file that reads a device, prints to one, or calls `exit`.

using CsvKit

const PROGRAM = "{{ npm_name }}"

"""Reads the whole input, from FILE or standard input."""
function read_input(path::AbstractString)
    return path == "" || path == "-" ? read(stdin, String) : read(path, String)
end

"""Formats a number for the summary report."""
function format_number(value)
    value isa Float64 || return string(value)
    isinteger(value) && return string(Int(value))
    return string(round(value, digits=6))
end

"""Turns one command line into an exit code: 0 success, 1 bad input, 2 usage."""
function main(argv::Vector{String})
    options = parse_args(argv)

    if options.status === :help
        print(stdout, usage(PROGRAM))
        return 0
    elseif options.status === :version
        println(stdout, version())
        return 0
    elseif options.status === :error
        println(stderr, "error: ", options.message)
        println(stderr)
        print(stderr, usage(PROGRAM))
        return 2
    end

    try
        text = read_input(options.file)
        table = parse_csv(text; delimiter=options.delimiter)
        options.command === :summary || (table = select_columns(table, options.columns))

        if options.command === :summary
            for (key, value) in column_summary(table, options.columns[1])
                println(stdout, key, "=", format_number(value))
            end
        elseif options.command === :json
            println(stdout, to_json(table))
        else
            print(stdout, render_csv(table))
        end
        return 0
    catch error
        error isa SystemError || error isa CsvError || rethrow()
        println(stderr, "error: ", sprint(showerror, error))
        return 1
    end
end

exit(main(ARGS))
