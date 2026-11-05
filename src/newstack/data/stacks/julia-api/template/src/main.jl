using HTTP
using TextstatApi

const DEFAULT_PORT = 8080

"""
    handler(request) -> HTTP.Response

Translate one `HTTP.Request` into the pure `TextstatApi.route` call, so the
server file only touches the socket.
"""
function handler(request::HTTP.Request)
    target = HTTP.URI(request.target)
    method = string(request.method)
    path = isempty(target.path) ? "/" : target.path
    query = something(target.query, "")
    body = String(request.body)
    reply = TextstatApi.route(method, path, query, body)
    return HTTP.Response(
        reply.status,
        ["Content-Type" => "application/json", "Connection" => "close"],
        reply.body,
    )
end

port = parse(Int, get(ENV, "PORT", string(DEFAULT_PORT)))
host = get(ENV, "ADDR", "127.0.0.1")
println("listening on http://$host:$port")
HTTP.serve(handler, host, port)
