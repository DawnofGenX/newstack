package {{ package_name }};

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.PrintStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

class CliTest {

    private final ByteArrayOutputStream out = new ByteArrayOutputStream();
    private final ByteArrayOutputStream err = new ByteArrayOutputStream();

    private int run(String stdin, String... args) {
        InputStream input = new ByteArrayInputStream(stdin.getBytes(StandardCharsets.UTF_8));
        return new Cli(input).run(args, new PrintStream(out, true), new PrintStream(err, true));
    }

    private String stdout() {
        return out.toString(StandardCharsets.UTF_8);
    }

    private String stderr() {
        return err.toString(StandardCharsets.UTF_8);
    }

    @Test
    @DisplayName("--help prints usage and exits 0")
    void helpExitsZero() {
        assertEquals(0, run("", "--help"));
        assertTrue(stdout().startsWith("usage:"), stdout());
    }

    @Test
    @DisplayName("--version prints the version and exits 0")
    void versionExitsZero() {
        assertEquals(0, run("", "--version"));
        assertEquals(Options.VERSION, stdout().trim());
    }

    @Test
    @DisplayName("with no file, stdin is counted and all three figures are printed")
    void countsStdin() {
        assertEquals(0, run("one two\nthree\n"));
        assertEquals("2       3      14", stdout().trim());
    }

    @Test
    @DisplayName("a mode flag prints one figure per file")
    void countsFileWithMode(@TempDir Path dir) throws IOException {
        Path file = dir.resolve("sample.txt");
        Files.writeString(file, "alpha beta gamma\n");
        assertEquals(0, run("", "-w", file.toString()));
        assertEquals("3 " + file, stdout().trim());
    }

    @Test
    @DisplayName("an unreadable file is reported and exits 1")
    void missingFileExitsOne(@TempDir Path dir) {
        int code = run("", dir.resolve("absent.txt").toString());
        assertEquals(1, code);
        assertTrue(stderr().contains("cannot open"), stderr());
    }

    @Test
    @DisplayName("a bad flag prints usage to stderr and exits 2")
    void badFlagExitsTwo() {
        assertEquals(2, run("", "--bogus"));
        assertTrue(stderr().contains("unknown option"), stderr());
        assertTrue(stderr().contains("usage:"), stderr());
        assertTrue(stdout().isEmpty(), "usage errors must not pollute stdout");
    }

    @Test
    @DisplayName("several files get a total line")
    void totalsMultipleFiles(@TempDir Path dir) throws IOException {
        Path first = dir.resolve("a.txt");
        Path second = dir.resolve("b.txt");
        Files.writeString(first, "a b\n");
        Files.writeString(second, "c\n");
        assertEquals(0, run("", "-l", first.toString(), second.toString()));
        String[] rows = stdout().strip().split("\\R");
        assertEquals(3, rows.length, stdout());
        assertTrue(rows[2].endsWith("total"), stdout());
    }
}
