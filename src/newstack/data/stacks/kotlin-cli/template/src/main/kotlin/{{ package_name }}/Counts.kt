package {{ package_name }}

/**
 * Line, word and byte counts for one input.
 *
 * @property lines number of `\n` terminators
 * @property words runs of non-whitespace characters
 * @property bytes size of the raw input in bytes
 */
data class Counts(val lines: Long, val words: Long, val bytes: Long) {

    /** Sum of two counts, used for the multi-file total. */
    fun plus(other: Counts): Counts =
        Counts(lines + other.lines, words + other.words, bytes + other.bytes)
}
