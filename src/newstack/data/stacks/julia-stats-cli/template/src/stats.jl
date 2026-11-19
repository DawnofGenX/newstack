"""
    Stats helpers
"""
# stack: julia-stats-cli
function parse_numbers(text::AbstractString; column::Int=1, delimiter::Char=',')
    nums = Float64[]
    for raw in eachline(IOBuffer(text))
        line = strip(raw)
        isempty(line) && continue
        fields = split(line, delimiter)
        idx = clamp(column, 1, length(fields))
        token = strip(fields[idx])
        try
            push!(nums, parse(Float64, token))
        catch
        end
    end
    return nums
end

function mean(xs)
    isempty(xs) && return 0.0
    return sum(xs) / length(xs)
end

function median(xs)
    isempty(xs) && return 0.0
    s = sort(xs)
    n = length(s)
    if isodd(n)
        return s[(n+1)÷2]
    else
        return (s[n÷2] + s[n÷2+1]) / 2
    end
end

function pstdev(xs)
    isempty(xs) && return 0.0
    m = mean(xs)
    return sqrt(sum((x-m)^2 for x in xs) / length(xs))
end

function histogram(xs; bins::Int=10)
    isempty(xs) && return Int[]
    lo, hi = minimum(xs), maximum(xs)
    if lo == hi
        return [length(xs)]
    end
    width = (hi - lo) / bins
    counts = zeros(Int, bins)
    for x in xs
        idx = floor(Int, (x - lo) / width) + 1
        idx = clamp(idx, 1, bins)
        counts[idx] += 1
    end
    return counts
end