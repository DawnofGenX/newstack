package {{ package_name }}

import java.io.File

fun main(args: Array<String>) {
    val code = run(args.toList(), { System.`in`.bufferedReader().readText() }, { println(it) }, { System.err.println(it) })
    kotlin.system.exitProcess(code)
}

fun run(args: List<String>, stdin: () -> String, out: (String) -> Unit, err: (String) -> Unit): Int {
    if (args.isEmpty() || args.contains("-h") || args.contains("--help")) {
        out("usage: {{ npm_name }} PATH_EXPR [--file FILE]\n\nEvaluate a JSONPath expression against JSON read from stdin or --file.\nExit codes: 0 success, 1 bad input, 2 usage error.\n")
        return 0
    }
    val pathExpr = args.firstOrNull { !it.startsWith("--") } ?: run {
        err("missing path expression")
        return 2
    }
    val file = args.firstOrNull { it.startsWith("--file=") }?.substringAfter("=")
        ?: args.zipWithNext().firstOrNull { it.first == "--file" }?.second
    val text = if (file != null) {
        try { File(file).readText() } catch (e: Exception) { err("cannot read file: ${e.message}"); return 1 }
    } else {
        try { stdin() } catch (e: Exception) { err("cannot read stdin: ${e.message}"); return 1 }
    }
    val root = try { Json.parse(text) } catch (e: Exception) { err("invalid json: ${e.message}"); return 1 }
    val results = try { JsonPath.evaluate(pathExpr, root) } catch (e: Exception) { err("bad path: ${e.message}"); return 2 }
    for (r in results) out(r.toJson())
    return 0
}
