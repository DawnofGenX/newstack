package {{ package_name }}

import java.io.File

fun main(args: Array<String>) {
    val path = args.getOrElse(0) { "-" }
    val text = if (path == "-") System.`in`.bufferedReader().readText() else File(path).readText()
    val table = Csv.parse(text)
    if (table.headers.isEmpty()) {
        println("rows=0")
        return
    }
    val groupCol = args.firstOrNull { it.startsWith("--group=") }?.substringAfter("=")
        ?: (table.headers.firstOrNull() ?: "")
    val sumCol = args.firstOrNull { it.startsWith("--sum=") }?.substringAfter("=")

    println("rows=${table.rows.size}")
    Report.groupCount(table, groupCol).forEach { (k, v) -> println("$k $v") }
    if (sumCol != null) {
        println("sum=${Report.sum(table, sumCol)}")
    }
}