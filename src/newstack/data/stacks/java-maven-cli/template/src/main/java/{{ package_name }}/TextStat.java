package {{ package_name }};

import java.nio.charset.StandardCharsets;

/** Pure counting logic, with no I/O so it can be tested directly. */
public final class TextStat {

    private TextStat() {
        // static helpers only
    }

    /** Counts the raw bytes, and decodes them as UTF-8 to count lines and words. */
    public static Counts count(byte[] data) {
        String text = new String(data, StandardCharsets.UTF_8);
        long lines = 0;
        long words = 0;
        boolean inWord = false;
        for (int index = 0; index < text.length(); index++) {
            char current = text.charAt(index);
            if (current == '\n') {
                lines++;
            }
            if (Character.isWhitespace(current)) {
                inWord = false;
            } else if (!inWord) {
                inWord = true;
                words++;
            }
        }
        return new Counts(lines, words, data.length);
    }

    /** Convenience overload for tests and callers that already hold text. */
    public static Counts count(String text) {
        return count(text.getBytes(StandardCharsets.UTF_8));
    }
}
