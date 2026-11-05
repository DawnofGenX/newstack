package textstat

/** Byte-exact counting with wc(1) rules, in one place. */
class Counts {
    int lines
    int words
    int bytes

    static Counts of(String text) {
        int lines = 0
        int words = 0
        boolean inWord = false
        // A Groovy String is UTF-16 in memory, so bytes must be measured from
        // the UTF-8 encoding, not from length().
        byte[] encoded = text.getBytes('UTF-8')
        for (byte raw : encoded) {
            int value = raw < 0 ? raw + 256 : raw
            if (value == 10) {
                lines++
            }
            if (value == 32 || value == 9 || value == 10 || value == 13 || value == 11 || value == 12) {
                inWord = false
            } else if (!inWord) {
                words++
                inWord = true
            }
        }
        return new Counts(lines: lines, words: words, bytes: encoded.length)
    }
}
