package com.example.textstat;

import java.nio.charset.StandardCharsets;
import org.springframework.stereotype.Service;

/**
 * Pure wc-style counting logic, with no I/O so it can be tested directly.
 */
@Service
public class StatsService {

    /** Counts lines, words and bytes of the given text, like {@code wc -lwc}. */
    public Stats count(String text) {
        byte[] data = text.getBytes(StandardCharsets.UTF_8);
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
        return new Stats(lines, words, data.length);
    }
}
