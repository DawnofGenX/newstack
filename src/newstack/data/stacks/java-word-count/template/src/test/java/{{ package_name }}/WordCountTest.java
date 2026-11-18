package {{ package_name }};

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;

class WordCountTest {

    @Test
    void normaliseLowercasesAndStripsPunctuation() {
        assertEquals("hello", WordCount.normalise("Hello,"));
        assertEquals("dont", WordCount.normalise("Don'T!"));
        assertEquals("", WordCount.normalise("--"));
        assertEquals("caf\u00e9", WordCount.normalise("Caf\u00e9"));
    }

    @Test
    void countsWordsAcrossPunctuationAndNewlines() {
        WordCount counter = WordCount.of("the cat sat\non the mat. The end!");
        assertEquals(3, counter.count("the"));
        assertEquals(1, counter.count("cat"));
        assertEquals(8, counter.total());
        assertEquals(6, counter.distinct());
    }

    @Test
    void unknownWordsCountAsZero() {
        WordCount counter = WordCount.of("alpha beta");
        assertEquals(0, counter.count("gamma"));
        assertEquals(2, counter.total());
    }

    @Test
    void topSortsByCountThenAlphabetically() {
        WordCount counter = WordCount.of("b a b c a b");
        List<Map.Entry<String, Long>> ranked = counter.top(3);
        assertEquals("b", ranked.get(0).getKey());
        assertEquals(3L, ranked.get(0).getValue());
        assertEquals("a", ranked.get(1).getKey());
        assertEquals("c", ranked.get(2).getKey());
    }

    @Test
    void topClampsTheLimit() {
        WordCount counter = WordCount.of("one two three");
        assertEquals(2, counter.top(2).size());
        assertEquals(3, counter.top(99).size());
        assertTrue(counter.top(0).isEmpty());
    }

    @Test
    void renderListsEveryWord() {
        WordCount counter = WordCount.of("x y x");
        assertEquals("x 2\ny 1\n", counter.render());
    }

    @Test
    void countsAreUnmodifiable() {
        WordCount counter = WordCount.of("a");
        try {
            counter.counts().put("b", 1L);
            throw new AssertionError("expected an unmodifiable map");
        } catch (UnsupportedOperationException expected) {
            assertEquals(1, counter.counts().size());
        }
    }

    @Test
    void emptyTextHasNoWords() {
        WordCount counter = WordCount.of("   \n\t ");
        assertEquals(0, counter.total());
        assertEquals(0, counter.distinct());
        assertEquals("", counter.render());
    }
}
