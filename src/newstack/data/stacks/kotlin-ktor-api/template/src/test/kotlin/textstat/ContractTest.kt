package textstat

import java.net.HttpURLConnection
import java.net.ServerSocket
import java.net.URLEncoder
import org.junit.jupiter.api.AfterAll
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.BeforeAll
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.parallel.Execution
import org.junit.jupiter.api.parallel.ExecutionMode

/**
 * Contract tests against a REAL socket: the same shaded code path --selftest
 * asserts at unit level, exercised over HTTP on an ephemeral port.
 */
class ContractTest {
    companion object {
        private var port: Int = -1
        private lateinit var thread: Thread

        @JvmStatic
        @BeforeAll
        fun up() {
            port = ServerSocket(0).use { it.localPort }
            thread = Thread { Server.startAndWait(port) }.also {
                it.isDaemon = true
                it.start()
            }
            val deadline = System.currentTimeMillis() + 15_000
            while (!healthy()) {
                if (System.currentTimeMillis() > deadline) error("server did not start on :$port")
                Thread.sleep(50)
            }
        }

        @JvmStatic
        @AfterAll
        fun down() {
            // engine owns its shutdown; interrupt the starter thread only
            thread.interrupt()
        }

        private fun healthy(): Boolean = runCatching {
            val (status, _) = exchange("GET", "/health", null, null)
            status == 200
        }.getOrDefault(false)

        private data class Resp(val status: Int, val body: String)

        private fun exchange(method: String, path: String, query: String?, body: String?): Resp {
            val url = "http://127.0.0.1:$port$path" + (query?.let { "?$it" } ?: "")
            val conn = (java.net.URI(url).toURL().openConnection() as HttpURLConnection).apply {
                requestMethod = method
                connectTimeout = 5_000
                readTimeout = 5_000
                doInput = true
            }
            if (body != null) {
                conn.doOutput = true
                conn.getOutputStream().use { it.write(body.toByteArray(Charsets.UTF_8)) }
            }
            val status = conn.responseCode
            val stream = if (status < 400) conn.inputStream else conn.errorStream
            val text = stream?.bufferedReader(Charsets.UTF_8)?.use { it.readText() } ?: ""
            conn.disconnect()
            return Resp(status, text)
        }
    }

    @Test fun healthExactBody() {
        val r = exchange("GET", "/health", null, null)
        assertEquals(200, r.status)
        assertEquals("{\"status\":\"ok\"}", r.body)
    }

    @Test fun getStatsFixtureTaskExact() {
        // "a b\n" -> 1/2/4 via query encoding (+ is space, %0A newline)
        val r = exchange("GET", "/stats", "text=a+b%0A", null)
        assertEquals(200, r.status)
        assertEquals("{\"text\":\"a b\\n\",\"lines\":1,\"words\":2,\"bytes\":4}", r.body)
    }

    @Test fun getStatsUtf8PercentEncoding() {
        val r = exchange("GET", "/stats", "text=h%C3%A9llo+w%C3%B6rld%0A", null)
        assertEquals(200, r.status)
        assertEquals("{\"text\":\"héllo wörld\\n\",\"lines\":1,\"words\":2,\"bytes\":14}", r.body)
    }

    @Test fun getStatsUtf8ViaURLEncoder() {
        val encoded = URLEncoder.encode("a b\nc\n", "UTF-8")
        val r = exchange("GET", "/stats", "text=$encoded", null)
        assertEquals(200, r.status)
        assertEquals("{\"text\":\"a b\\nc\\n\",\"lines\":2,\"words\":3,\"bytes\":6}", r.body)
    }

    @Test fun getStatsMissingTextIs422() {
        val r = exchange("GET", "/stats", "x=1", null)
        assertEquals(422, r.status)
        assertEquals("{\"error\":\"missing_text\"}", r.body)
    }

    @Test fun getStatsEmptyTextIsZeroes() {
        val r = exchange("GET", "/stats", "text=", null)
        assertEquals(200, r.status)
        assertEquals("{\"text\":\"\",\"lines\":0,\"words\":0,\"bytes\":0}", r.body)
    }

    @Test fun firstTextParamWinsOverSocket() {
        val r = exchange("GET", "/stats", "text=one&text=two", null)
        assertEquals(200, r.status)
        assertEquals("{\"text\":\"one\",\"lines\":0,\"words\":1,\"bytes\":3}", r.body)
    }

    @Test fun postStatsExactBody() {
        val r = exchange("POST", "/stats", null, "{\"text\":\"a b\\n\"}")
        assertEquals(200, r.status)
        assertEquals("{\"text\":\"a b\\n\",\"lines\":1,\"words\":2,\"bytes\":4}", r.body)
    }

    @Test fun postStatsMissingMember() {
        val r = exchange("POST", "/stats", null, "{\"other\":1}")
        assertEquals(422, r.status)
        assertEquals("{\"error\":\"missing_text\"}", r.body)
    }

    @Test fun postStatsNonStringText() {
        val r = exchange("POST", "/stats", null, "{\"text\":42}")
        assertEquals(422, r.status)
        assertEquals("{\"error\":\"invalid_json\"}", r.body)
    }

    @Test fun postStatsMalformedJson() {
        val r = exchange("POST", "/stats", null, "{\"text\":\"a\"")
        assertEquals(422, r.status)
        assertEquals("{\"error\":\"invalid_json\"}", r.body)
    }

    @Test fun wrongMethodOnHealth() {
        val r = exchange("POST", "/health", null, "{}")
        assertEquals(405, r.status)
        assertEquals("{\"error\":\"method_not_allowed\"}", r.body)
    }

    @Test fun wrongMethodOnStats() {
        val r = exchange("PUT", "/stats", null, null)
        assertEquals(405, r.status)
        assertEquals("{\"error\":\"method_not_allowed\"}", r.body)
    }

    @Test fun unknownPath404WithStrippedQuery() {
        val r = exchange("GET", "/nope", "text=x", null)
        assertEquals(404, r.status)
        assertEquals("{\"error\":\"not_found\",\"detail\":\"no route for GET /nope\"}", r.body)
    }

    @Test fun trailingSlashHealthIsUnknown() {
        val r = exchange("GET", "/health/", null, null)
        assertEquals(404, r.status)
        assertEquals("{\"error\":\"not_found\",\"detail\":\"no route for GET /health/\"}", r.body)
    }

    @Test fun malformedPercentDecodeDegradesToLiteral() {
        // java.net.URI rejects %zz, so hand the server raw HTTP bytes.
        // Do NOT close() the output stream — that closes the socket before read.
        val sock = java.net.Socket("127.0.0.1", port)
        try {
            sock.getOutputStream().write(
                "GET /stats?text=%zz HTTP/1.1\r\nHost: x\r\nConnection: close\r\n\r\n".toByteArray()
            )
            sock.getOutputStream().flush()
            val raw = sock.getInputStream().bufferedReader(Charsets.UTF_8).readText()
            assertEquals(true, raw.contains("{\"text\":\"%zz\",\"lines\":0,\"words\":1,\"bytes\":3}"))
        } finally {
            sock.close()
        }
    }
}
