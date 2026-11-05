package textstat

import com.sun.net.httpserver.HttpServer

import java.nio.charset.StandardCharsets

/** Serves the route table over com.sun.net.httpserver, one connection at a time. */
class Server {
    static void serve(String host, int port) {
        HttpServer server = HttpServer.create(new InetSocketAddress(host, port), 16)
        server.createContext('/', { exchange ->
            String method = exchange.requestMethod
            String path = exchange.requestURI.path
            String query = exchange.requestURI.rawQuery
            String body = exchange.requestBody.getText('UTF-8')
            Reply reply = Contract.route(method, path, query == null ? '' : query, body)
            byte[] payload = reply.body.getBytes(StandardCharsets.UTF_8)
            exchange.responseHeaders.add('content-type', 'application/json')
            exchange.sendResponseHeaders(reply.status, payload.length as long)
            exchange.responseBody.withCloseable { stream -> stream.write(payload) }
        } as com.sun.net.httpserver.HttpHandler)
        server.start()
        println "listening on http://${host}:${port}"
        System.out.flush()
    }
}
