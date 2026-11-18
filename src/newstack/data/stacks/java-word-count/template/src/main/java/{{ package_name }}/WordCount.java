package {{ package_name }};

import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

/** Counts word frequencies with a deterministic ordering. */
public final class WordCount {

    private final Map<String, Long> counts = new LinkedHashMap<>();
    private long total;

    /** Counts every word in {@code text}. */
    public static WordCount of(String text) {
        WordCount result = new WordCount();
        result.addText(text);
        return result;
    }

    /** Lowercases and strips everything that is not a letter or digit. */
    public static String normalise(String word) {
        StringBuilder builder = new StringBuilder(word.length());
        word.toLowerCase(Locale.ROOT)
                .codePoints()
                .filter(Character::isLetterOrDigit)
                .forEach(builder::appendCodePoint);
        return builder.toString();
    }

    /** Counts the words of a whole document. */
    public void addText(String text) {
        StringBuilder word = new StringBuilder();
        for (int index = 0; index < text.length(); index++) {
            char character = text.charAt(index);
            if (Character.isLetterOrDigit(character)) {
                word.append(character);
            } else {
                flush(word);
            }
        }
        flush(word);
    }

    private void flush(StringBuilder word) {
        if (word.length() == 0) {
            return;
        }
        add(word.toString());
        word.setLength(0);
    }

    /** Records one occurrence of {@code word}. */
    public void add(String word) {
        String normalised = normalise(word);
        if (normalised.isEmpty()) {
            return;
        }
        counts.merge(normalised, 1L, Long::sum);
        total++;
    }

    /** How many times {@code word} appeared, compared case-insensitively. */
    public long count(String word) {
        return counts.getOrDefault(normalise(word), 0L);
    }

    /** Number of distinct words. */
    public long distinct() {
        return counts.size();
    }

    /** Number of words counted in total, duplicates included. */
    public long total() {
        return total;
    }

    /** An unmodifiable snapshot of the raw counts, in first-seen order. */
    public Map<String, Long> counts() {
        return Collections.unmodifiableMap(new LinkedHashMap<>(counts));
    }

    /** The {@code limit} most frequent words, ties broken alphabetically. */
    public List<Map.Entry<String, Long>> top(int limit) {
        if (limit < 1) {
            return List.of();
        }
        List<Map.Entry<String, Long>> ranked = new ArrayList<>(counts.entrySet());
        ranked.sort(Comparator.<Map.Entry<String, Long>>comparingLong(Map.Entry::getValue)
                .reversed()
                .thenComparing(Map.Entry::getKey));
        return List.copyOf(ranked.subList(0, Math.min(limit, ranked.size())));
    }

    /** Renders the full ranking as {@code word count} lines. */
    public String render() {
        StringBuilder builder = new StringBuilder();
        for (Map.Entry<String, Long> entry : top(counts.size())) {
            builder.append(entry.getKey()).append(' ').append(entry.getValue()).append('\n');
        }
        return builder.toString();
    }
}
