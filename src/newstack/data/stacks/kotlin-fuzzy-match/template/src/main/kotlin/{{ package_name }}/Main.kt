package {{ package_name }}

import kotlin.system.exitProcess

private const val USAGE = """usage: {{ npm_name }} --a TEXT --b TEXT [--threshold VALUE]
       {{ npm_name }} --a TEXT --list one,two,three"""

fun main(args: Array<String>) {
    var left: String? = null
    var right: String? = null
    var list: String? = null
    var threshold = 0.0

    var index = 0
    while (index < args.size) {
        val flag = args[index]
        val value = args.getOrNull(index + 1)
        when (flag) {
            "--a" -> left = value ?: usageError("--a needs a value")
            "--b" -> right = value ?: usageError("--b needs a value")
            "--list" -> list = value ?: usageError("--list needs a value")
            "--threshold" -> threshold = value?.toDoubleOrNull() ?: usageError("--threshold needs a number")
            "-h", "--help" -> {
                println(USAGE)
                return
            }
            else -> usageError("unknown option $flag")
        }
        index += 2
    }

    val target = left ?: usageError("--a is required")

    if (list != null) {
        val candidates = list.split(',').map { it.trim() }.filter { it.isNotEmpty() }
        if (candidates.isEmpty()) usageError("--list needs at least one entry")
        JaroWinkler.rank(target, candidates).forEachIndexed { position, (candidate, score) ->
            println("rank %d: %s %.4f".format(position + 1, candidate, score))
        }
        return
    }

    val other = right ?: usageError("--b or --list is required")
    val score = JaroWinkler.winkler(target, other)
    println("jaro=%.4f jaro-winkler=%.4f match=%s".format(JaroWinkler.jaro(target, other), score, score >= threshold))
}

private fun usageError(message: String): Nothing {
    System.err.println("error: $message")
    System.err.println(USAGE)
    exitProcess(2)
}
