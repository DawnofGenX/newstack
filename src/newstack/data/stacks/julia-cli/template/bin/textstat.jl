#!/usr/bin/env julia
#
# The runnable command: argv in, figures out, an exit code back. This is the
# only file that reads a device, prints to one, or calls `exit`; everything it
# decides lives in the Textstat module.

using Textstat

const PROGRAM = "{{ npm_name }}"

"""Prints one row of figures for `counts`, padded like `wc`."""
function print_counts(io::IO, mode::Symbol, counts::Counts, label::AbstractString)
    figures = String[]
    if mode === :all || mode === :lines
        push!(figures, lpad(counts.lines, 8))
    end
    if mode === :all || mode === :words
        push!(figures, lpad(counts.words, 8))
    end
    if mode === :all || mode === :bytes
        push!(figures, lpad(counts.bytes, 8))
    end
    row = join(figures, " ")
    isempty(label) || (row = string(row, " ", label))
    println(io, row)
    return nothing
end

"""Counts every requested file, prints a total for more than one, reports failures."""
function count_files(mode::Symbol, files::Vector{String})
    total = Counts(0, 0, 0)
    failed = false

    for path in files
        try
            data = path == "-" ? read(stdin, String) : read(path, String)
            counted = counts(data)
            print_counts(stdout, mode, counted, path == "-" ? "" : path)
            total += counted
        catch error
            println(stderr, "error: cannot read '", path, "': ", sprint(showerror, error))
            failed = true
        end
    end

    length(files) > 1 && print_counts(stdout, mode, total, "total")
    return failed ? 1 : 0
end

"""Turns one command line into an exit code: 0 success, 1 unreadable input, 2 usage."""
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

    if isempty(options.files)
        print_counts(stdout, options.mode, counts(read(stdin, String)), "")
        return 0
    end

    return count_files(options.mode, options.files)
end

exit(main(ARGS))
