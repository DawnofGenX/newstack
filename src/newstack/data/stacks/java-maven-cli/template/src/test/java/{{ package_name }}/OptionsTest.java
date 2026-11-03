package {{ package_name }};

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.List;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

class OptionsTest {

    @Test
    @DisplayName("no flags means all three counts and no files")
    void defaults() {
        Options options = Options.parse(new String[0]);
        assertEquals(Options.Status.OK, options.status());
        assertEquals(Options.Mode.ALL, options.mode());
        assertTrue(options.files().isEmpty());
    }

    @Test
    @DisplayName("short and long spellings select the same mode")
    void modeSpellings() {
        assertEquals(Options.Mode.LINES, Options.parse(new String[] {"-l"}).mode());
        assertEquals(Options.Mode.WORDS, Options.parse(new String[] {"--words"}).mode());
        assertEquals(Options.Mode.BYTES, Options.parse(new String[] {"-c"}).mode());
    }

    @Test
    @DisplayName("two different modes are a usage error")
    void conflictingModes() {
        Options options = Options.parse(new String[] {"-l", "-w"});
        assertEquals(Options.Status.ERROR, options.status());
        assertTrue(options.error().contains("conflicts"), options.error());
    }

    @Test
    @DisplayName("the same mode twice is accepted")
    void repeatedModeIsFine() {
        assertEquals(Options.Status.OK, Options.parse(new String[] {"-w", "--words"}).status());
    }

    @Test
    @DisplayName("an unknown option is a usage error that names it")
    void unknownOption() {
        Options options = Options.parse(new String[] {"--nope"});
        assertEquals(Options.Status.ERROR, options.status());
        assertTrue(options.error().contains("--nope"), options.error());
    }

    @Test
    @DisplayName("--help and -V stop parsing")
    void helpAndVersion() {
        assertEquals(Options.Status.HELP, Options.parse(new String[] {"--help"}).status());
        assertEquals(Options.Status.VERSION, Options.parse(new String[] {"-V"}).status());
    }

    @Test
    @DisplayName("everything after -- is a file name, even if it looks like a flag")
    void doubleDashStopsOptionParsing() {
        Options options = Options.parse(new String[] {"--", "-l", "notes.txt"});
        assertEquals(Options.Status.OK, options.status());
        assertEquals(List.of("-l", "notes.txt"), options.files());
    }

    @Test
    @DisplayName("- is accepted as the stdin placeholder")
    void dashIsAFile() {
        assertEquals(List.of("-"), Options.parse(new String[] {"-"}).files());
    }
}
