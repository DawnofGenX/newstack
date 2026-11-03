package {{ package_name }};

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

class TextStatTest {

    @Test
    @DisplayName("empty input counts nothing")
    void emptyInput() {
        assertEquals(new Counts(0, 0, 0), TextStat.count(new byte[0]));
    }

    @Test
    @DisplayName("a trailing newline closes the last line")
    void multiLine() {
        Counts counts = TextStat.count("one two\nthree\n");
        assertEquals(2, counts.lines());
        assertEquals(3, counts.words());
        assertEquals(14, counts.bytes());
    }

    @Test
    @DisplayName("a final line without a newline is not counted as a line")
    void unterminatedLastLine() {
        Counts counts = TextStat.count("alpha beta");
        assertEquals(0, counts.lines());
        assertEquals(2, counts.words());
        assertEquals(10, counts.bytes());
    }

    @Test
    @DisplayName("runs of spaces and tabs are one word boundary")
    void collapsesWhitespace() {
        Counts counts = TextStat.count("a  b\tc\r\nd");
        assertEquals(4, counts.words());
        assertEquals(1, counts.lines());
    }

    @Test
    @DisplayName("bytes are counted on the UTF-8 encoding, not on characters")
    void countsUtf8Bytes() {
        Counts counts = TextStat.count("h\u00e9llo\n");
        assertEquals(1, counts.lines());
        assertEquals(1, counts.words());
        assertEquals(7, counts.bytes());
    }

    @Test
    @DisplayName("counts add up for a multi-file total")
    void addsCounts() {
        Counts total = TextStat.count("a b\n").plus(TextStat.count("c\n"));
        assertEquals(new Counts(2, 3, 6), total);
    }
}
