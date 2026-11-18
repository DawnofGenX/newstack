package {{ package_name }}

// kotlin-csv-report

import java.io.File

data class CsvTable(val headers: List<String>, val rows: List<List<String>>)

object Csv {
    fun parse(text: String): CsvTable {
        val lines = text.trimEnd('\n').split("\n").filter { it.isNotBlank() }
        if (lines.isEmpty()) return CsvTable(emptyList(), emptyList())
        val rows = lines.map { parseLine(it) }
        val headers = rows.first()
        return CsvTable(headers, rows.drop(1))
    }

    private fun parseLine(line: String): List<String> {
        val fields = mutableListOf<String>()
        val sb = StringBuilder()
        var inQuotes = false
        var i = 0
        while (i < line.length) {
            val c = line[i]
            when {
                c == '"' -> {
                    if (inQuotes && i + 1 < line.length && line[i + 1] == '"') {
                        sb.append('"')
                        i++
                    } else {
                        inQuotes = !inQuotes
                    }
                }
                c == ',' && !inQuotes -> {
                    fields.add(sb.toString())
                    sb.setLength(0)
                }
                else -> sb.append(c)
            }
            i++
        }
        fields.add(sb.toString())
        return fields
    }

    fun readFile(path: String): CsvTable = parse(File(path).readText())
}

object Report {
    fun indexOf(table: CsvTable, column: String): Int {
        val idx = table.headers.indexOf(column)
        require(idx >= 0) { "unknown column: $column" }
        return idx
    }

    fun groupCount(table: CsvTable, column: String): Map<String, Int> {
        val idx = indexOf(table, column)
        val counts = linkedMapOf<String, Int>()
        for (row in table.rows) {
            val key = row.getOrElse(idx) { "" }
            counts[key] = (counts[key] ?: 0) + 1
        }
        return counts.toSortedMap()
    }

    fun sum(table: CsvTable, column: String): Double {
        val idx = indexOf(table, column)
        return table.rows.sumOf { row -> row.getOrElse(idx) { "0" }.toDoubleOrNull() ?: 0.0 }
    }
}