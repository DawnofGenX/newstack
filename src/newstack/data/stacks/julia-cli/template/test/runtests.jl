using Test

using Textstat

const PROJECT = dirname(@__DIR__)
const SCRIPT = joinpath(PROJECT, "bin", "textstat.jl")

"""Run the real entry script as a child process so exit codes are the ones a
user gets, not a value this test file invented."""
function run_cli(args::Vector{String}; input::Union{Nothing,String}=nothing)
    cmd = addenv(
        `$(Base.julia_cmd()) --startup-file=no --color=no $(SCRIPT) $(args)`,
        "JULIA_PROJECT" => PROJECT,
    )
    if input === nothing
        return run(pipeline(ignorestatus(cmd), stdout=devnull, stderr=devnull))
    end
    return run(pipeline(
        ignorestatus(cmd),
        stdin=IOBuffer(input),
        stdout=devnull,
        stderr=devnull,
    ))
end

@testset "counts" begin
    @testset "empty input has no lines, words or bytes" begin
        @test counts("") == Counts(0, 0, 0)
    end

    @testset "trailing newline ends the line it terminates" begin
        @test counts("one two\nthree\n") == Counts(2, 3, 14)
    end

    @testset "no trailing newline counts one line fewer" begin
        @test counts("one two\nthree") == Counts(1, 3, 13)
    end

    @testset "runs of whitespace separate words but are not words" begin
        @test counts("a   b\tc\n\n") == Counts(2, 3, 9)
    end

    @testset "bytes are counted, not characters" begin
        @test counts("héllo\n") == Counts(1, 1, 7)
    end

    @testset "totals add componentwise" begin
        @test Counts(1, 2, 3) + Counts(4, 5, 6) == Counts(5, 7, 9)
    end
end

@testset "options" begin
    @testset "no arguments means every figure from standard input" begin
        options = parse_args(String[])
        @test options.mode === :all
        @test isempty(options.files)
        @test options.status === :ok
    end

    @testset "short and long modes agree" begin
        @test parse_args(["-l"]).mode === :lines
        @test parse_args(["--lines"]).mode === :lines
        @test parse_args(["-w"]).mode === :words
        @test parse_args(["--words"]).mode === :words
        @test parse_args(["-c"]).mode === :bytes
        @test parse_args(["--bytes"]).mode === :bytes
    end

    @testset "files keep their order" begin
        @test parse_args(["--words", "a.txt", "b.txt"]).files == ["a.txt", "b.txt"]
    end

    @testset "a dash is a file, not an option" begin
        @test parse_args(["-"]).files == ["-"]
    end

    @testset "-- stops option parsing" begin
        @test parse_args(["--", "-l"]).files == ["-l"]
        @test parse_args(["--", "-l"]).status === :ok
    end

    @testset "help and version are statuses, not errors" begin
        @test parse_args(["-h"]).status === :help
        @test parse_args(["--help"]).status === :help
        @test parse_args(["-V"]).status === :version
        @test parse_args(["--version"]).status === :version
    end

    @testset "repeating the same mode is allowed" begin
        @test parse_args(["-l", "-l"]).status === :ok
        @test parse_args(["-l", "-l"]).mode === :lines
    end

    @testset "conflicting modes are a usage error" begin
        options = parse_args(["-l", "-w"])
        @test options.status === :error
        @test occursin("conflicts", options.message)
    end

    @testset "unknown options are a usage error" begin
        options = parse_args(["--bogus"])
        @test options.status === :error
        @test occursin("unknown option '--bogus'", options.message)
    end

    @testset "help text names the program it was invoked as" begin
        @test startswith(usage("textstat"), "usage: textstat")
        @test occursin("--bytes", usage("textstat"))
    end
end

@testset "exit codes" begin
    @testset "--help succeeds" begin
        @test run_cli(["--help"]).exitcode == 0
    end

    @testset "bad usage exits 2" begin
        @test run_cli(["--bogus"]).exitcode == 2
    end

    @testset "a missing file exits 1" begin
        @test run_cli(["does-not-exist.txt"]).exitcode == 1
    end

    @testset "standard input with no file succeeds" begin
        @test run_cli(String[]; input="one two\n").exitcode == 0
    end
end
