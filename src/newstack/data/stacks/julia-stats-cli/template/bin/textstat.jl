#!/usr/bin/env julia

using Textstat

const PROGRAM = "{{ npm_name }}"

function main(argv)
    column = 1
    bins = 10
    files = String[]
    i = 1
    while i <= length(argv)
        a = argv[i]
        if a == "--help" || a == "-h"
            println("usage: $PROGRAM [--column N] [--bins N] [FILE ...]")
            return 0
        elseif a == "--version"
            println("0.1.0")
            return 0
        elseif a == "--column"
            column = parse(Int, argv[i+1]); i += 2; continue
        elseif a == "--bins"
            bins = parse(Int, argv[i+1]); i += 2; continue
        else
            push!(files, a); i += 1
        end
    end
    if isempty(files); files = ["-"]; end
    for path in files
        data = path == "-" ? read(stdin, String) : read(path, String)
        nums = parse_numbers(data; column=column)
        println("count=$(length(nums))")
        println("mean=$(mean(nums))")
        println("median=$(median(nums))")
        println("pstdev=$(pstdev(nums))")
        println("min=$(isempty(nums) ? 0.0 : minimum(nums))")
        println("max=$(isempty(nums) ? 0.0 : maximum(nums))")
        println("histogram=$(histogram(nums; bins=bins))")
    end
    return 0
end

exit(main(ARGS))