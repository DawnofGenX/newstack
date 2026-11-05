"""One HTTP answer: a status code and a JSON body."""
struct Reply
    status::Int
    body::String
end

error_reply(status::Int, code::AbstractString) =
    Reply(status, JSON3.write((error = code,)))

error_reply(status::Int, code::AbstractString, detail::AbstractString) =
    Reply(status, JSON3.write((error = code, detail = detail)))

stats_reply(text::AbstractString) = begin
    counts = count_text(text)
    Reply(
        200,
        JSON3.write((
            text = String(text),
            lines = counts.lines,
            words = counts.words,
            bytes = counts.bytes,
        )),
    )
end

"""
    query_param(query, name) -> Union{String,Nothing}

The decoded value of the first `name` in a raw query string, or `nothing` when
the parameter is absent. `%20` and `%0A` are decoded; an absent `=` means the
empty value.
"""
function query_param(query::AbstractString, name::AbstractString)
    for pair in split(query, '&'; keepempty = false)
        parts = split(pair, '='; limit = 2)
        key = HTTP.URIs.unescapeuri(first(parts))
        if key == name
            return length(parts) == 2 ? HTTP.URIs.unescapeuri(parts[2]) : ""
        end
    end
    return nothing
end

"""
    route(method, path, query, body) -> Reply

The whole HTTP surface as a pure function, so every status code is testable
without a socket: `GET /health`, `GET /stats?text=`, `POST /stats` with a JSON
body, 405 for the two known paths under another method, 404 for anything else.
"""
function route(
    method::AbstractString,
    path::AbstractString,
    query::AbstractString,
    body::AbstractString,
)::Reply
    if path == "/health" && method == "GET"
        return Reply(200, JSON3.write((status = "ok",)))
    elseif path == "/stats" && method == "GET"
        text = query_param(query, "text")
        text === nothing && return error_reply(422, "missing_text")
        return stats_reply(text)
    elseif path == "/stats" && method == "POST"
        parsed = try
            JSON3.read(body)
        catch
            nothing
        end
        parsed isa JSON3.Object || return error_reply(422, "invalid_json")
        haskey(parsed, :text) || return error_reply(422, "missing_text")
        text = parsed.text
        text isa AbstractString || return error_reply(422, "missing_text")
        return stats_reply(text)
    elseif path == "/health" || path == "/stats"
        return error_reply(405, "method_not_allowed")
    end
    return error_reply(404, "not_found", "no route for $method $path")
end
