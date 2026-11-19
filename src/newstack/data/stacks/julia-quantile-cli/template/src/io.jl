const VERSION = "0.1.0"

function usage(program)
    return """Usage: $program [OPTION]... FILE [P]

Compute a quantile (default p=0.5) or mean of numeric data.

  --mean           arithmetic mean
  --weighted-mean  weighted mean; FILE has 'value weight' pairs
  -h, --help       show this help
      --version    show version
"""
end

function run(args::Vector{String})
    program = "{{ npm_name }}"
    if isempty(args) || args[1] in ("-h", "--help")
        print(stdout, usage(program))
        return 0
    end
    if args[1] == "--version"
        println(stdout, VERSION)
        return 0
    end

    weighted = false
    meanmode = false
    i = 1
    while i <= length(args) && startswith(args[i], "--")
        if args[i] == "--weighted-mean"
            weighted = true
        elseif args[i] == "--mean"
            meanmode = true
        else
            println(stderr, "error: unknown option $(args[i])")
            return 2
        end
        i += 1
    end

    if i > length(args)
        println(stderr, "error: missing file")
        return 2
    end
    path = args[i]
    i += 1
    p = 0.5
    if !weighted && !meanmode && i <= length(args)
        try
            p = parse(Float64, args[i])
        catch
            println(stderr, "error: invalid probability $(args[i])")
            return 2
        end
    end

    text = try
        path == "-" ? read(stdin, String) : read(path, String)
    catch e
        println(stderr, "error: cannot read '$path': $e")
        return 1
    end

    if weighted
        xs = Float64[]
        ws = Float64[]
        for line in split(text, '\n')
            toks = split(line)
            isempty(toks) && continue
            length(toks) < 2 && (println(stderr, "error: expected value weight"); return 2)
            push!(xs, parse(Float64, toks[1]))
            push!(ws, parse(Float64, toks[2]))
        end
        println(stdout, weighted_mean(xs, ws))
        return 0
    elseif meanmode
        vals = parse_numbers(text)
        println(stdout, sum(vals) / length(vals))
        return 0
    else
        vals = parse_numbers(text)
        println(stdout, quantile(vals, p))
        return 0
    end
end
