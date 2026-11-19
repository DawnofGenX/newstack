"""
    Options

A parsed command line: the command, the columns to keep, the delimiter, and how
far parsing got. Parsing never prints and never exits.
"""
struct Options
    command::Symbol
    columns::Vector{String}
    delimiter::Char
    json::Bool
    file::String
    status::Symbol
    message::String
end

function Options(;
    command::Symbol=:print,
    columns::AbstractVector{<:AbstractString}=String[],
    delimiter::Char=',',
    json::Bool=false,
    file::AbstractString="",
    status::Symbol=:ok,
    message::AbstractString="",
)
    return Options(command, String[String(column) for column in columns], delimiter, json,
                   String(file), status, String(message))
end

"""The version reported by `--version`."""
const VERSION = "0.1.0"

version() = VERSION

"""A short description of the delimiter accepted by the tool."""
function delimiter_for(spec::AbstractString)
    spec == "tab" && return '\t'
    spec == "\\t" && return '\t'
    spec == "comma" && return ','
    spec == "semicolon" && return ';'
    spec == "pipe" && return '|'
    length(spec) == 1 || return nothing
    return first(spec)
end

"""The text printed by `--help`."""
function usage(program::AbstractString)
    return """usage: $program [options] [FILE]

Read CSV, then print it, pick columns, or summarise a column.  With no FILE, or
when FILE is -, read standard input.

Commands
  --print          write the table back out (the default)
  --json           write the table as JSON
  --summary COL    statistics for one column, by name or 1-based position
  --columns LIST   keep only these columns, comma separated, in this order
  --delimiter D    input and output delimiter: a character, tab, or symbol
  --out-delimiter D
                   write with a different delimiter than the one read
  -h, --help       show this message
  -V, --version    show the version

Exit codes: 0 success, 1 bad input, 2 usage.
"""
end

"""
    parse_args(args) -> Options

Hand-rolled argv parsing: no dependency, and every branch is a unit test.
"""
function parse_args(args::Vector{String})
    command = :print
    columns = String[]
    delimiter = ','
    out_delimiter = ','
    json = false
    file = ""
    index = 1
    only_files = false

    function fail(message::AbstractString)
        return Options(; command=command, columns=columns, delimiter=delimiter,
                       json=json, file=file, status=:error, message=String(message))
    end

    while index <= length(args)
        argument = args[index]
        index += 1

        if only_files
            isempty(file) || return fail("only one FILE may be given")
            file = argument
            continue
        end
        if argument == "--"
            only_files = true
            continue
        elseif argument in ("-h", "--help")
            return Options(; status=:help)
        elseif argument in ("-V", "--version")
            return Options(; status=:version)
        elseif argument == "--print"
            command = :print
        elseif argument == "--json"
            command = :json
            json = true
        elseif argument in ("--summary", "--columns", "--delimiter", "--out-delimiter")
            index <= length(args) || return fail("$argument needs a value")
            value = args[index]
            index += 1
            if argument == "--summary"
                command = :summary
                push!(columns, value)
            elseif argument == "--columns"
                append!(columns, split(value, ','))
            elseif argument == "--delimiter"
                parsed = delimiter_for(value)
                parsed === nothing && return fail("unknown delimiter '$value'")
                delimiter = parsed
            else
                parsed = delimiter_for(value)
                parsed === nothing && return fail("unknown delimiter '$value'")
                out_delimiter = parsed
            end
        elseif startswith(argument, "-") && argument != "-"
            return fail("unknown option '$argument'")
        else
            isempty(file) || return fail("only one FILE may be given")
            file = argument
        end
    end

    if command === :summary && length(columns) > 1
        return fail("--summary takes exactly one column")
    end
    return Options(; command=command, columns=columns, delimiter=delimiter, json=json, file=file)
end
