using Test
using HTTP
using JSON3
using TextstatApi

const CASES = [
    ("", (0, 0, 0)),
    ("hello world\n", (1, 2, 12)),
    ("a b\nc\n", (2, 3, 6)),
    ("\n\nx\n", (3, 1, 4)),
    ("  \t ", (0, 0, 4)),
    ("héllo wörld\n", (1, 2, 14)),
    ("🙂\n", (1, 1, 5)),
]

@testset "count_text counts the way wc does" begin
    for (text, expected) in CASES
        counts = count_text(text)
        @test (counts.lines, counts.words, counts.bytes) == expected
    end
    @test_throws MethodError count_text(42)
end

@testset "health" begin
    reply = route("GET", "/health", "", "")
    @test reply.status == 200
    @test JSON3.read(reply.body).status == "ok"
end

@testset "GET /stats" begin
    reply = route("GET", "/stats", "text=hello%20world%0A", "")
    @test reply.status == 200
    payload = JSON3.read(reply.body)
    @test payload.text == "hello world\n"
    @test (payload.lines, payload.words, payload.bytes) == (1, 2, 12)

    empty_text = route("GET", "/stats", "text=", "")
    @test JSON3.read(empty_text.body).lines == 0

    missing = route("GET", "/stats", "", "")
    @test missing.status == 422
    @test JSON3.read(missing.body).error == "missing_text"
end

@testset "POST /stats" begin
    reply = route("POST", "/stats", "", "{\"text\":\"a b\\nc\\n\"}")
    @test reply.status == 200
    payload = JSON3.read(reply.body)
    @test payload.text == "a b\nc\n"
    @test (payload.lines, payload.words, payload.bytes) == (2, 3, 6)

    padded = route("POST", "/stats", "", "{\"text\":\"  padded  \\n\"}")
    @test (JSON3.read(padded.body).lines, JSON3.read(padded.body).bytes) == (1, 11)

    @test route("POST", "/stats", "", "{}").status == 422
    @test JSON3.read(route("POST", "/stats", "", "{}").body).error == "missing_text"

    not_a_string = route("POST", "/stats", "", "{\"text\":42}")
    @test not_a_string.status == 422
    @test JSON3.read(not_a_string.body).error == "missing_text"

    broken = route("POST", "/stats", "", "{not json")
    @test broken.status == 422
    @test JSON3.read(broken.body).error == "invalid_json"

    scalar = route("POST", "/stats", "", "\"just a string\"")
    @test scalar.status == 422
end

@testset "everything else" begin
    gone = route("GET", "/nope", "", "")
    @test gone.status == 404
    @test JSON3.read(gone.body).error == "not_found"
    @test JSON3.read(gone.body).detail == "no route for GET /nope"

    wrong_method = route("DELETE", "/health", "", "")
    @test wrong_method.status == 405
    @test JSON3.read(wrong_method.body).error == "method_not_allowed"
end

@testset "over a real socket" begin
    port = 54_111
    server = HTTP.serve!(request -> HTTP.Response(
        200,
        ["Content-Type" => "application/json"],
        route(
            string(request.method),
            HTTP.URI(request.target).path,
            something(HTTP.URI(request.target).query, ""),
            String(request.body),
        ).body,
    ), "127.0.0.1", port)
    try
        response = HTTP.get("http://127.0.0.1:$port/stats?text=hello%20world%0A")
        @test response.status == 200
        @test JSON3.read(response.body).bytes == 12
    finally
        close(server)
    end
end
