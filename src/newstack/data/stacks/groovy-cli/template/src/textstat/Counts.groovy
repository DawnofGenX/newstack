package textstat

/**
 * The counting core. Everything works on bytes, so a multi-byte character
 * counts as several bytes exactly like wc does.
 */
class Counts {
    static final List<Integer> WHITESPACE = [32, 9, 10, 13, 11, 12].asImmutable()

    final long lines
    final long words
    final long bytes

    Counts(long lines, long words, long bytes) {
        this.lines = lines
        this.words = words
        this.bytes = bytes
    }

    static Counts empty() {
        new Counts(0L, 0L, 0L)
    }

    static Counts of(byte[] data) {
        long lines = 0L
        long words = 0L
        boolean inWord = false
        for (int index = 0; index < data.length; index++) {
            int value = data[index] & 0xFF
            if (value == 10) {
                lines += 1L
            }
            boolean isSpace = WHITESPACE.contains(value)
            if (!isSpace && !inWord) {
                words += 1L
            }
            inWord = !isSpace
        }
        return new Counts(lines, words, (long) data.length)
    }

    Counts plus(Counts other) {
        return new Counts(lines + other.lines, words + other.words, bytes + other.bytes)
    }

    long figure(String name) {
        switch (name) {
            case 'lines':
                return lines
            case 'words':
                return words
            default:
                return bytes
        }
    }

    List<Long> columns(List<String> figures) {
        return figures.collect { String name -> figure(name) }
    }
}
