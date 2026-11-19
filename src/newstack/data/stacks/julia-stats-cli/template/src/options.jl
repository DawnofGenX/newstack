"""
    Options

A parsed command line: which mode was chosen, which files to read, and how far
parsing got. Parsing never prints and never exits; `status` tells the entry
point what to do next.
"""
struct Options
    mode::Symbol
    files::Vector{String}
    status::Symbol
    message::String
end

function Options(;
    mode::Symbol=:all,
    files::AbstractVector{<:AbstractString}=String[],
    status::Symbol=:ok,
    message::AbstractString="",
)
    return Options(mode, String[String(file) for file in files], status, String(message))
end

"""The version reported by `--version`."""
const VERSION = "0.1.0"

"""Package version, as a function so callers need not read the constant."""
version() = VERSION

function _mode_for(argument::AbstractString)
    argument in ("-l", "--lines") && return :lines
    argument in ("-w", "--words") && return :words
    argument in ("-c", "--bytes") && return :bytes
    return nothing
end

"""
    parse_args(args) -> Options

Hand-rolled argv parsing: no dependency, and every branch is a unit test.
Options stop being special after `--`, and `-` names standard input rather
than an option.
"""
function parse_args(args::AbstractVector{<:AbstractString})
    mode = :all
    chosen = false
    only_files = false
    files = String[]

    for raw in args
        argument = String(raw)

        if only_files || isempty(argument) || argument == "-"
            push!(files, argument)
            continue
        end

        if argument == "--"
            only_files = true
            continue
        end

        if argument in ("-h", "--help")
            return Options(; mode=mode, files=files, status=:help)
        end

        if argument in ("-V", "--version")
            return Options(; mode=mode, files=files, status=:version)
        end

        requested = _mode_for(argument)
        if requested !== nothing
            if chosen && requested != mode
                return Options(
                    ;
                    mode=mode,
                    files=files,
                    status=:error,
                    message="choose one of -l, -w, -c: '$argument' conflicts with an earlier mode",
                )
            end
            mode = requested
            chosen = true
            continue
        end

        if startswith(argument, "-")
            return Options(
                ;
                mode=mode,
                files=files,
                status=:error,
                message="unknown option '$argument'",
            )
        end

        push!(files, argument)
    end

    return Options(; mode=mode, files=files, status=:ok)
end

"""
    usage(program) -> String

Help text; the caller supplies the name it was invoked as, so the banner
matches the script that is actually running.
"""
function usage(program::AbstractString)
    return string(
        "usage: ", program, " [-l | -w | -c] [--] [FILE ...]\n",
        "\n",
        "Count lines, words and bytes in each FILE, or in standard input\n",
        "when no FILE is given. With more than one FILE a total is printed.\n",
        "\n",
        "  -l, --lines     print the line count only\n",
        "  -w, --words     print the word count only\n",
        "  -c, --bytes     print the byte count only\n",
        "  -h, --help      show this help and exit\n",
        "  -V, --version   show the version and exit\n",
    )
end
