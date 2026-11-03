package {{ package_name }}

import java.io.ByteArrayInputStream
import java.io.ByteArrayOutputStream
import java.io.InputStream
import java.io.PrintStream
import java.nio.charset.StandardCharsets
import java.nio.file.Files
import java.nio.file.Path
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.DisplayName
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.io.TempDir

class CliTest {

    private val out = ByteArrayOutputStream()
    private val err = ByteArrayOutputStream()

    private fun run(stdin: String, vararg args: String): Int {
        val input: InputStream = ByteArrayInputStream(stdin.toByteArray(StandardCharsets.UTF_8))
        return Cli(input).run(arrayOf(*args), PrintStream(out, true), PrintStream(err, true))
    }

    private fun stdout(): String = out.toString(StandardCharsets.UTF_8)

    private fun stderr(): String = err.toString(StandardCharsets.UTF_8)

    @Test
    @DisplayName("--help prints usage and exits 0")
    fun helpExitsZero() {
        assertEquals(0, run("", "--help"))
        assertTrue(stdout().startsWith("usage:"), stdout())
    }

    @Test
    @DisplayName("--version prints the version and exits 0")
    fun versionExitsZero() {
        assertEquals(0, run("", "--version"))
        assertEquals(Options.VERSION, stdout().trim())
    }

    @Test
    @DisplayName("with no file, stdin is counted and all three figures are printed")
    fun countsStdin() {
        assertEquals(0, run("one two\nthree\n"))
        assertEquals("2       3      14", stdout().trim())
    }

    @Test
    @DisplayName("a mode flag prints one figure per file")
    fun countsFileWithMode(@TempDir dir: Path) {
        val file = dir.resolve("sample.txt")
        Files.writeString(file, "alpha beta gamma\n")
        assertEquals(0, run("", "-w", file.toString()))
        assertEquals("3 $file", stdout().trim())
    }

    @Test
    @DisplayName("an unreadable file is reported and exits 1")
    fun missingFileExitsOne(@TempDir dir: Path) {
        assertEquals(1, run("", dir.resolve("absent.txt").toString()))
        assertTrue(stderr().contains("cannot open"), stderr())
    }

    @Test
    @DisplayName("a bad flag prints usage to stderr and exits 2")
    fun badFlagExitsTwo() {
        assertEquals(2, run("", "--bogus"))
        assertTrue(stderr().contains("unknown option"), stderr())
        assertTrue(stderr().contains("usage:"), stderr())
        assertTrue(stdout().isEmpty(), "usage errors must not pollute stdout")
    }

    @Test
    @DisplayName("several files get a total line")
    fun totalsMultipleFiles(@TempDir dir: Path) {
        val first = dir.resolve("a.txt")
        val second = dir.resolve("b.txt")
        Files.writeString(first, "a b\n")
        Files.writeString(second, "c\n")
        assertEquals(0, run("", "-l", first.toString(), second.toString()))
        val rows = stdout().trim().split(Regex("\\R"))
        assertEquals(3, rows.size, stdout())
        assertTrue(rows[2].endsWith("total"), stdout())
    }
}
