package {{ package_name }}

/** Which figures to print; `ALL` prints lines, words and bytes. */
enum class Mode {
    ALL,
    LINES,
    WORDS,
    BYTES,
}

/** How argument parsing ended. */
enum class Status {
    OK,
    HELP,
    VERSION,
    ERROR,
}

/** Parsed command line: the chosen mode, the files, and how parsing ended. */
data class Options(
    val mode: Mode,
    val files: List<String>,
    val status: Status,
    val error: String = "",
) {

    companion object {
        const val VERSION = "0.1.0"

        /** Hand-rolled parser: no dependency, and every branch is unit tested. */
        fun parse(args: Array<String>): Options {
            var chosen: Mode? = null
            var onlyFiles = false
            val files = mutableListOf<String>()

            for (arg in args) {
                if (onlyFiles || arg.isEmpty() || arg == "-") {
                    files.add(arg)
                    continue
                }
                if (arg == "--") {
                    onlyFiles = true
                    continue
                }
                if (arg == "-h" || arg == "--help") {
                    return Options(chosenOrAll(chosen), files, Status.HELP)
                }
                if (arg == "-V" || arg == "--version") {
                    return Options(chosenOrAll(chosen), files, Status.VERSION)
                }
                val requested = modeFor(arg)
                if (requested != null) {
                    if (chosen != null && chosen != requested) {
                        return Options(
                            chosen,
                            files,
                            Status.ERROR,
                            "choose one of -l, -w, -c: '$arg' conflicts with an earlier mode",
                        )
                    }
                    chosen = requested
                    continue
                }
                if (arg.startsWith("-")) {
                    return Options(
                        chosenOrAll(chosen),
                        files,
                        Status.ERROR,
                        "unknown option '$arg'",
                    )
                }
                files.add(arg)
            }
            return Options(chosenOrAll(chosen), files, Status.OK)
        }

        private fun chosenOrAll(chosen: Mode?): Mode = chosen ?: Mode.ALL

        private fun modeFor(arg: String): Mode? = when (arg) {
            "-l", "--lines" -> Mode.LINES
            "-w", "--words" -> Mode.WORDS
            "-c", "--bytes" -> Mode.BYTES
            else -> null
        }

        /** Help text; the program name comes from the artifact so it matches the jar. */
        fun usage(program: String): String = buildString {
            append("usage: ").append(program).append(" [-l | -w | -c] [--] [FILE ...]\n")
            append("\n")
            append("Count lines, words and bytes in each FILE, or in standard input\n")
            append("when no FILE is given. With more than one FILE a total is printed.\n")
            append("\n")
            append("  -l, --lines     print the line count only\n")
            append("  -w, --words     print the word count only\n")
            append("  -c, --bytes     print the byte count only\n")
            append("  -h, --help      show this help and exit\n")
            append("  -V, --version   show the version and exit\n")
        }
    }
}
