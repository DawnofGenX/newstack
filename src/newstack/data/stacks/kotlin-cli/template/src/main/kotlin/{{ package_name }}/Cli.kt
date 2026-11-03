package {{ package_name }}

import java.io.IOException
import java.io.InputStream
import java.io.PrintStream
import java.nio.file.Files
import java.nio.file.Path

/**
 * The runnable command: turns argv into output and an exit code.
 *
 * Nothing here calls `exitProcess`, so tests drive [run] directly.
 * Exit codes: `0` success, `1` unreadable input, `2` bad usage.
 */
class Cli(private val stdin: InputStream) {

    fun run(args: Array<String>, out: PrintStream, err: PrintStream): Int {
        val options = Options.parse(args)
        when (options.status) {
            Status.HELP -> {
                out.print(Options.usage(PROGRAM))
                return 0
            }
            Status.VERSION -> {
                out.println(Options.VERSION)
                return 0
            }
            Status.ERROR -> {
                err.println("error: " + options.error)
                err.println()
                err.print(Options.usage(PROGRAM))
                return 2
            }
            Status.OK -> Unit
        }

        val mode = options.mode
        val files = options.files
        if (files.isEmpty()) {
            val counts = try {
                TextStat.count(stdin.readBytes())
            } catch (exc: IOException) {
                err.println("error: cannot read standard input: " + exc.message)
                return 1
            }
            print(out, counts, mode, "")
            return 0
        }

        var total = Counts(0, 0, 0)
        var failed = false
        for (path in files) {
            if (path == "-") {
                val counts = try {
                    TextStat.count(stdin.readBytes())
                } catch (exc: IOException) {
                    err.println("error: cannot read standard input: " + exc.message)
                    failed = true
                    continue
                }
                print(out, counts, mode, "")
                total = total.plus(counts)
            } else {
                val counts = try {
                    TextStat.count(Files.readAllBytes(Path.of(path)))
                } catch (exc: IOException) {
                    err.println("error: cannot open '$path'")
                    failed = true
                    continue
                }
                print(out, counts, mode, path)
                total = total.plus(counts)
            }
        }

        if (files.size > 1) {
            print(out, total, mode, "total")
        }
        return if (failed) 1 else 0
    }

    private fun print(out: PrintStream, counts: Counts, mode: Mode, label: String) {
        val line = StringBuilder()
        if (mode == Mode.ALL || mode == Mode.LINES) {
            line.append(String.format("%8d", counts.lines))
        }
        if (mode == Mode.ALL || mode == Mode.WORDS) {
            line.append(String.format("%8d", counts.words))
        }
        if (mode == Mode.ALL || mode == Mode.BYTES) {
            line.append(String.format("%8d", counts.bytes))
        }
        if (label.isNotEmpty()) {
            line.append(' ').append(label)
        }
        out.println(line)
    }

    companion object {
        private const val PROGRAM = "{{ npm_name }}"
    }
}
