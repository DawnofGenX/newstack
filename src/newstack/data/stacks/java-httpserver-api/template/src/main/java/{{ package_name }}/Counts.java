package {{ package_name }};

import java.nio.charset.StandardCharsets;

/** The three numbers the service reports, counted exactly as wc does. */
public record Counts(int lines, int words, int bytes) {

    /** Counts one UTF-8 string: line = '\n', word = maximal non-space run, bytes = UTF-8. */
    public static Counts of(String text) {
        if (text == null) {
            throw new IllegalArgumentException("countText expects a string, got null");
        }
        int lines = 0;
        int words = 0;
        int bytes = text.getBytes(StandardCharsets.UTF_8).length;
        boolean inWord = false;
        for (int i = 0; i < text.length(); i++) {
            char c = text.charAt(i);
            if (c == '\n') {
                lines++;
            }
            if (isSpace(c)) {
                inWord = false;
            } else if (!inWord) {
                inWord = true;
                words++;
            }
        }
        return new Counts(lines, words, bytes);
    }

    private static boolean isSpace(char c) {
        return c == ' ' || c == '\t' || c == '\n' || c == '\r' || c == 0x0b || c == 0x0c;
    }
}
