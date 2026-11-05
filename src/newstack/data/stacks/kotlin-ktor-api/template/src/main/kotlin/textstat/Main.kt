package textstat

/** Entry point: `--selftest` runs offline; otherwise serve on 127.0.0.1. */
fun main(args: Array<String>) {
    if (args.contains("--selftest")) {
        val failures = SelfTest.run()
        System.exit(failures)
    }

    val port = Contract.resolvePort(System.getenv("PORT"))
    if (port == null) {
        System.err.println("blog-count: PORT must be a number in 1..65535")
        kotlin.system.exitProcess(2)
    }

    System.err.println("blog-count: listening on http://127.0.0.1:$port")
    Server.startAndWait(port)
}
