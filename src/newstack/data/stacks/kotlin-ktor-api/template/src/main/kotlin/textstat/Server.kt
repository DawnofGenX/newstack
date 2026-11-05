package textstat

import io.ktor.http.ContentType
import io.ktor.http.HttpStatusCode
import io.ktor.http.withCharset
import io.ktor.serialization.kotlinx.json.json
import io.ktor.server.application.Application
import io.ktor.server.application.ApplicationCallPipeline
import io.ktor.server.application.install
import io.ktor.server.engine.embeddedServer
import io.ktor.server.netty.Netty
import io.ktor.server.plugins.contentnegotiation.ContentNegotiation
import io.ktor.server.request.httpMethod
import io.ktor.server.request.path
import io.ktor.server.request.receiveText
import io.ktor.server.request.uri
import io.ktor.server.response.respondText

/**
 * Ktor 3 translation layer. Every HTTP decision lives in Contract.kt, so the
 * offline --selftest suite and this server cannot drift apart.
 *
 * Raw interception on the Setup phase (not the Routing plugin) is deliberate:
 * Ktor 3's default 404/405 bodies would violate the exact-body contract, and
 * Routing would also serve "/health/" style variants we must reject.
 */
fun Application.textStatModule() {
    // Proves the content-negotiation + kotlinx serializer stack is really wired in.
    install(ContentNegotiation) {
        json(kotlinx.serialization.json.Json { ignoreUnknownKeys = true })
    }

    // Application *is* the ApplicationCallPipeline in Ktor 3; intercept is a member.
    intercept(ApplicationCallPipeline.Setup) {
        val call = context
        val request = call.request
        val method = request.httpMethod.value.uppercase()
        val query = if ('?' in request.uri) request.uri.substringAfter('?') else null
        val body = if (method == "POST") runCatching { call.receiveText() }.getOrDefault("") else ""
        val outcome = Contract.dispatch(method, request.path(), query, body)
        call.respondText(
            outcome.body,
            ContentType.Application.Json.withCharset(Charsets.UTF_8),
            HttpStatusCode.fromValue(outcome.status)
        )
        finish()
    }
}

object Server {
    /** Return type inferred: embeddedServer yields EmbeddedServer<NettyApplicationEngine, ...>. */
    fun newServer(port: Int) =
        embeddedServer(Netty, host = "127.0.0.1", port = port) {
            textStatModule()
        }

    /** Ktor 3's JVM engine hooks SIGTERM/SIGINT itself; start(wait) blocks until shutdown. */
    fun startAndWait(port: Int) {
        newServer(port).start(wait = true)
    }
}
