package {{ package_name }}

import java.io.File

fun main(args: Array<String>) {
    val path = args.firstOrNull { !it.startsWith("--") }
    if (path == null) {
        println("usage: {{ npm_name }} LEDGER.csv")
        println("each line is account,amount with a negative amount for a debit")
        return
    }
    val ledger = Ledger()
    File(path).readLines()
        .map { it.trim() }
        .filter { it.isNotEmpty() && !it.startsWith("#") }
        .forEachIndexed { index, line ->
            val parts = line.split(",").map { it.trim() }
            require(parts.size == 2) { "line ${index + 1} must be account,amount: $line" }
            ledger.post(parts[0], Money.parse(parts[1]))
        }
    ledger.report().forEach { println(it) }
    println("total ${ledger.trialBalance().format()}")
}
