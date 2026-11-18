package {{ package_name }}

import java.io.File

const val USAGE = """Usage: {{ npm_name }} <encode|decode> [value] [options]

Options:
  --file PATH   read the input from PATH instead of the value
  --hex         treat the value as hexadecimal (decode: print hex output)
  -h, --help    show this message

Without a value the input is read from stdin. Missing arguments exit 2, an
invalid payload exits 1.
"""

fun run(args: List<String>, stdin: () -> String, out: (String) -> Unit, err: (String) -> Unit): Int {
    if (args.isEmpty() || args[0] == "-h" || args[0] == "--help") {
        out(USAGE)
        return if (args.isEmpty()) 2 else 0
    }
    val command = args[0]
    if (command != "encode" && command != "decode") {
        err("{{ npm_name }}: unknown command $command")
        return 2
    }
    var value: String? = null
    var path: String? = null
    var hex = false
    var index = 1
    while (index < args.size) {
        when (val argument = args[index]) {
            "-h", "--help" -> {
                out(USAGE)
                return 0
            }
            "--hex" -> hex = true
            "--file" -> {
                index += 1
                path = args.getOrNull(index) ?: run {
                    err("{{ npm_name }}: --file needs a path")
                    return 2
                }
            }
            else -> {
                if (argument.startsWith("-") && argument != "-") {
                    err("{{ npm_name }}: unknown option $argument")
                    return 2
                }
                value = if (argument == "-") null else argument
            }
        }
        index += 1
    }
    val raw = when {
        path != null -> File(path).readText()
        value != null -> value
        else -> stdin()
    }
    return try {
        if (command == "encode") {
            val bytes = if (hex) hexToBytes(raw.trim()) else raw.trimEnd('\n').toByteArray()
            out(Base32.encode(bytes))
        } else {
            val bytes = Base32.decode(raw)
            out(if (hex) bytes.joinToString("") { "%02x".format(it) } else String(bytes))
        }
        0
    } catch (error: Base32.Base32Exception) {
        err("{{ npm_name }}: ${error.message}")
        1
    } catch (error: NumberFormatException) {
        err("{{ npm_name }}: invalid hexadecimal input")
        1
    }
}

fun hexToBytes(text: String): ByteArray {
    val digits = text.filterNot { it.isWhitespace() }
    if (digits.length % 2 != 0) {
        throw Base32.Base32Exception("hex input needs an even number of digits")
    }
    return ByteArray(digits.length / 2) { index ->
        digits.substring(index * 2, index * 2 + 2).toInt(16).toByte()
    }
}

fun main(args: Array<String>) {
    val code = run(args.toList(), { System.`in`.bufferedReader().readText() }, { println(it) }, { System.err.println(it) })
    if (code != 0) {
        kotlin.system.exitProcess(code)
    }
}
