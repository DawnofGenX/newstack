function weighted_mean(xs::AbstractVector{<:Real}, ws::AbstractVector{<:Real})
    length(xs) == length(ws) || error("length mismatch")
    isempty(xs) && error("empty input")
    total_w = sum(Float64(w) for w in ws)
    total_w == 0 && error("zero total weight")
    return sum(Float64(x) * Float64(w) for (x, w) in zip(xs, ws)) / total_w
end

function parse_numbers(text::AbstractString)
    values = Float64[]
    for token in split(text)
        push!(values, parse(Float64, token))
    end
    return values
end
