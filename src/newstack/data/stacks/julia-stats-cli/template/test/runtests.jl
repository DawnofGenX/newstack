using Test
using Textstat

@testset "stats" begin
    @test mean([1.0,2,3]) == 2.0
    @test median([1.0,2,3,4]) == 2.5
    @test pstdev([1.0,1,1]) == 0.0
    @test parse_numbers("1\n2,3\n4") == [1.0,2.0,4.0]
    @test parse_numbers("a,1\nb,2", column=2) == [1.0,2.0]
    @test histogram([1.0,2,3,10], bins=2) == [3,1]
end

const PROJECT = dirname(@__DIR__)
const SCRIPT = joinpath(PROJECT, "bin", "textstat.jl")
function run_cli(args; input=nothing)
    cmd = addenv(`$(Base.julia_cmd()) --startup-file=no --color=no $(SCRIPT) $(args)`, "JULIA_PROJECT" => PROJECT)
    if input === nothing
        return run(pipeline(ignorestatus(cmd), stdout=devnull, stderr=devnull))
    end
    return run(pipeline(ignorestatus(cmd), stdin=IOBuffer(input), stdout=devnull, stderr=devnull))
end

@testset "exit codes" begin
    @test run_cli(["--help"]).exitcode == 0
    @test run_cli(["--bins","2"]; input="1\n2\n").exitcode == 0
end