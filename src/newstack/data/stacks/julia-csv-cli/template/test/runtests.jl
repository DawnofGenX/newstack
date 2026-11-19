using Test

using CsvKit

const PROJECT = dirname(@__DIR__)
const SCRIPT = joinpath(PROJECT, "bin", "{{ npm_name }}.jl")

"""Run the real entry script as a child process so exit codes are the ones a
user gets, not a value this test file invented."""
function run_cli(args::Vector{String}; input::Union{Nothing,String}=nothing)
    cmd = addenv(
        `$(Base.julia_cmd()) --startup-file=no --color=no $(SCRIPT) $(args)`,
        "JULIA_PROJECT" => PROJECT,
    )
    process = if input === nothing
        run(pipeline(ignorestatus(cmd), stdout=devnull, stderr=devnull))
    else
        run(pipeline(ignorestatus(cmd), stdin=IOBuffer(input), stdout=devnull, stderr=devnull))
    end
    return process.exitcode
end

"""Run the entry script and capture stdout."""
function capture(args::Vector{String}; input::Union{Nothing,String}=nothing)
    cmd = addenv(
        `$(Base.julia_cmd()) --startup-file=no --color=no $(SCRIPT) $(args)`,
        "JULIA_PROJECT" => PROJECT,
    )
    buffer = IOBuffer()
    if input === nothing
        run(pipeline(ignorestatus(cmd), stdout=buffer, stderr=devnull))
    else
        run(pipeline(ignorestatus(cmd), stdin=IOBuffer(input), stdout=buffer, stderr=devnull))
    end
    return String(take!(buffer))
end

@testset "parse" begin
    simple = parse_csv("a,b\n1,2\n")
    @test simple.headers == ["a", "b"]
    @test simple.rows == [["1", "2"]]

    quoted = parse_csv("a,b\n\"x,y\",\"say \"\"hi\"\"\"\n")
    @test quoted.rows == [["x,y", "say \"hi\""]]

    embedded = parse_csv("a,b\n\"one\ntwo\",3\n")
    @test embedded.rows == [["one\ntwo", "3"]]

    crlf = parse_csv("a,b\r\n1,2\r\n")
    @test crlf.rows == [["1", "2"]]

    trailing = parse_csv("a,b\n1,2")
    @test trailing.rows == [["1", "2"]]

    semicolons = parse_csv("a;b\n1;2\n", delimiter=';')
    @test semicolons.rows == [["1", "2"]]

    @test_throws CsvError parse_csv("")
    @test_throws CsvError parse_csv("a,b\n1,2,3\n")
    @test_throws CsvError parse_csv("a,b\n\"open,2\n")

    ragged = try
        parse_csv("a,b\n1,2,3\n")
    catch error
        sprint(showerror, error)
    end
    @test occursin("line 2", ragged)
    @test occursin("3 fields, expected 2", ragged)
end

@testset "render" begin
    table = CsvTable(["a", "b"], [["plain", "x,y"], ["say \"hi\"", " padded "]])
    rendered = render_csv(table)
    @test startswith(rendered, "a,b\n")
    @test occursin("\"x,y\"", rendered)
    @test occursin("\"say \"\"hi\"\"\"", rendered)
    @test occursin("\" padded \"", rendered)
    @test parse_csv(rendered) == table
    @test render_csv(table; delimiter=';') |> line -> occursin(";", line)
end

@testset "columns" begin
    table = parse_csv("name,score,city\nalice,10,pune\nbob,7,mumbai\n")
    @test column_index(table, "score") == 2
    @test column_index(table, "3") == 3
    @test_throws CsvError column_index(table, "nope")
    @test_throws CsvError column_index(table, "4")

    picked = select_columns(table, ["city", "name"])
    @test picked.headers == ["city", "name"]
    @test picked.rows[1] == ["pune", "alice"]

    @test select_columns(table, String[]).headers == table.headers
end

@testset "summary and json" begin
    table = parse_csv("name,score\nalice,10\nbob,7\n")
    stats = Dict(column_summary(table, "score"))
    @test stats["count"] == 2
    @test stats["sum"] == 17.0
    @test stats["mean"] == 8.5
    @test stats["min"] == 7.0
    @test stats["max"] == 10.0

    names = Dict(column_summary(table, "name"))
    @test names["count"] == 2
    @test !haskey(names, "sum")

    @test to_json(table) == "[{\"name\":\"alice\",\"score\":\"10\"},{\"name\":\"bob\",\"score\":\"7\"}]"
    @test to_json(parse_csv("a\n\"q\"\"q\"\n")) == "[{\"a\":\"q\\\"q\"}]"
end

@testset "cli" begin
    @test run_cli(["--help"]) == 0
    @test run_cli(["-V"]) == 0
    @test run_cli(["--bogus"]) == 2
    @test run_cli(["does-not-exist.csv"]) == 1
    @test run_cli(["--delimiter"]) == 2
    @test run_cli(["--summary"]) == 2

    @test capture(["--json"]; input="a,b\n1,2\n") == "[{\"a\":\"1\",\"b\":\"2\"}]\n"
    @test capture(["--columns", "b"]; input="a,b\n1,2\n") == "b\n2\n"
    summary_output = capture(["--summary", "score"]; input="name,score\nalice,10\nbob,7\n")
    @test occursin("column=score", summary_output)
    @test occursin("mean=8.5", summary_output)
    @test capture(String[]; input="a,b\n1,2\n") == "a,b\n1,2\n"
end
