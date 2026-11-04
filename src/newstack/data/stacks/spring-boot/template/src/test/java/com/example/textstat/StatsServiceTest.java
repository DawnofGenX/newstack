package com.example.textstat;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

class StatsServiceTest {

    private final StatsService service = new StatsService();

    @Test
    @DisplayName("empty input counts nothing")
    void emptyInput() {
        Stats stats = service.count("");
        assertEquals(0, stats.lines());
        assertEquals(0, stats.words());
        assertEquals(0, stats.bytes());
    }

    @Test
    @DisplayName("a trailing newline closes the last line")
    void multiLine() {
        Stats stats = service.count("one two\nthree\n");
        assertEquals(2, stats.lines());
        assertEquals(3, stats.words());
        assertEquals(14, stats.bytes());
    }

    @Test
    @DisplayName("a final line without a newline is not counted as a line")
    void unterminatedLastLine() {
        Stats stats = service.count("alpha beta");
        assertEquals(0, stats.lines());
        assertEquals(2, stats.words());
        assertEquals(10, stats.bytes());
    }
}
