module Quantiles

include("quantile.jl")
include("weighted.jl")
include("io.jl")

export quantile, weighted_mean, parse_numbers, run

end
