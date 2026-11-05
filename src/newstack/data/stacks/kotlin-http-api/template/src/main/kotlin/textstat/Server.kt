package textstat

import com.sun.net.httpserver.HttpServer
import java.net.InetSocketAddress

/**
 * Socket/HTTP layer only. All decisions come from Contract.
 * TRAP: HttpExchange.requestURI percent-DECODES the path but leaves
 * rawQuery verbatim — we use rawPath+rawQuery so targets echo as sent.
 */
object Server {
    fun start(host: String, port: Int): HttpServer {
        val server = HttpServer.create(InetSocketAddress(host, port), 0)
        server.executor = null
        server.createContext("/") { ex ->
            try {
                val method = ex.requestMethod
                val uri = ex.requestURI
                val target = (uri.rawPath ?: "/") +
                    if (uri.rawQuery != null) "?${uri.rawQuery}" else ""
                val body = if (method == "POST" && target == "/stats")
                    ex.requestBody.readBytes() else ByteArray(0)
                val resp = if (method == "POST" && target == "/stats")
                    Contract.handlePost(body) else Contract.handle(method, target)
                val out = resp.body
                ex.responseHeaders.set("Content-Type", "application/json")
                ex.responseHeaders.set("connection", "close")
                ex.sendResponseHeaders(resp.status, out.size.toLong())
                ex.responseBody.use { it.write(out) }
            } catch (e: Exception) {
                val msg = """{"error":"internal"}""".toByteArray(Charsets.ISO_8859_1)
                runCatching {
                    ex.responseHeaders.set("Content-Type", "application/json")
                    ex.sendResponseHeaders(500, msg.size.toLong())
                    ex.responseBody.use { it.write(msg) }
                }
            }
        }
        server.start()
        return server
    }
}
