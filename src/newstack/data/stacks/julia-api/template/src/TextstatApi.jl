module TextstatApi

using HTTP
using JSON3

include("counts.jl")
include("contract.jl")

export Counts, Reply, count_text, route, query_param, stats_reply

end
