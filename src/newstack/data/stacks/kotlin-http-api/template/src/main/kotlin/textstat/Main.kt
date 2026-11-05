package textstat

import kotlin.system.exitProcess

/**
 * Entry point.
 *   --selftest -> run in-process checks; exit 0 all-ok, 1 any failure
 *   otherwise  -> serve; HOST env (default 127.0.0.1), PORT env (default 8080);
 *                 exit 2 on bad config.
 */
fun main(args: Array<String>) {
    if (args.contains("--selftest")) {
        exitProcess(if (SelfTest.run()) 0 else 1)
    }
    val host = System.getenv("HOST")?.ifBlank { null } ?: "127.0.0.1"
    val port = (System.getenv("PORT")?.ifBlank { null } ?: "8080").toIntOrNull()
        ?: run { System.err.println("bad PORT env"); exitProcess(2) }
    try {
        Server.start(host, port)
        println("serving http://$host:$port")
        Thread.currentThread().join()
    } catch (e: Exception) {
        System.err.println("bind failed: ${e.message}")
        exitProcess(2)
    }
}
