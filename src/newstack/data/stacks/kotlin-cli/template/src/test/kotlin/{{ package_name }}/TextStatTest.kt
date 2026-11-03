package {{ package_name }}

import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.DisplayName
import org.junit.jupiter.api.Test

class TextStatTest {

    @Test
    @DisplayName("empty input counts nothing")
    fun emptyInput() {
        assertEquals(Counts(0, 0, 0), TextStat.count(ByteArray(0)))
    }

    @Test
    @DisplayName("a trailing newline closes the last line")
    fun multiLine() {
        val counts = TextStat.count("one two\nthree\n")
        assertEquals(2, counts.lines)
        assertEquals(3, counts.words)
        assertEquals(14, counts.bytes)
    }

    @Test
    @DisplayName("a final line without a newline is not counted as a line")
    fun unterminatedLastLine() {
        val counts = TextStat.count("alpha beta")
        assertEquals(0, counts.lines)
        assertEquals(2, counts.words)
        assertEquals(10, counts.bytes)
    }

    @Test
    @DisplayName("runs of spaces and tabs are one word boundary")
    fun collapsesWhitespace() {
        val counts = TextStat.count("a  b\tc\r\nd")
        assertEquals(4, counts.words)
        assertEquals(1, counts.lines)
    }

    @Test
    @DisplayName("bytes are counted on the UTF-8 encoding, not on characters")
    fun countsUtf8Bytes() {
        val counts = TextStat.count("h\u00e9llo\n")
        assertEquals(1, counts.lines)
        assertEquals(1, counts.words)
        assertEquals(7, counts.bytes)
    }

    @Test
    @DisplayName("counts add up for a multi-file total")
    fun addsCounts() {
        val total = TextStat.count("a b\n").plus(TextStat.count("c\n"))
        assertEquals(Counts(2, 3, 6), total)
    }
}
