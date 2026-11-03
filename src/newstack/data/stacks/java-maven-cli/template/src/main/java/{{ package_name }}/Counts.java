package {{ package_name }};

/**
 * Line, word and byte counts for one input.
 *
 * @param lines number of {@code \n} terminators
 * @param words runs of non-whitespace characters
 * @param bytes size of the raw input in bytes
 */
public record Counts(long lines, long words, long bytes) {

    /** Sum of two counts, used for the multi-file total. */
    public Counts plus(Counts other) {
        return new Counts(lines + other.lines, words + other.words, bytes + other.bytes);
    }
}
