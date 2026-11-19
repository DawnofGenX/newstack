function quantile(sorted_xs::Vector{Float64}, p::Float64)
    isempty(sorted_xs) && error("empty input")
    (p < 0 || p > 1) && error("p out of range")
    n = length(sorted_xs)
    n == 1 && return sorted_xs[1]
    h = (n - 1) * p
    lo = floor(Int, h) + 1
    hi = ceil(Int, h) + 1
    if hi > n
        hi = n
    end
    if lo == hi
        return sorted_xs[lo]
    end
    frac = h - (lo - 1)
    return sorted_xs[lo] + (sorted_xs[hi] - sorted_xs[lo]) * frac
end

function quantile(xs::AbstractVector{<:Real}, p::Real=0.5)
    ys = sort(Float64[x for x in xs])
    return quantile(ys, Float64(p))
end
