package {{ package_name }}

import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.DisplayName
import org.junit.jupiter.api.Test

class OptionsTest {

    @Test
    @DisplayName("no flags means all three counts and no files")
    fun defaults() {
        val options = Options.parse(emptyArray())
        assertEquals(Status.OK, options.status)
        assertEquals(Mode.ALL, options.mode)
        assertTrue(options.files.isEmpty())
    }

    @Test
    @DisplayName("short and long spellings select the same mode")
    fun modeSpellings() {
        assertEquals(Mode.LINES, Options.parse(arrayOf("-l")).mode)
        assertEquals(Mode.WORDS, Options.parse(arrayOf("--words")).mode)
        assertEquals(Mode.BYTES, Options.parse(arrayOf("-c")).mode)
    }

    @Test
    @DisplayName("two different modes are a usage error")
    fun conflictingModes() {
        val options = Options.parse(arrayOf("-l", "-w"))
        assertEquals(Status.ERROR, options.status)
        assertTrue(options.error.contains("conflicts"), options.error)
    }

    @Test
    @DisplayName("the same mode twice is accepted")
    fun repeatedModeIsFine() {
        assertEquals(Status.OK, Options.parse(arrayOf("-w", "--words")).status)
    }

    @Test
    @DisplayName("an unknown option is a usage error that names it")
    fun unknownOption() {
        val options = Options.parse(arrayOf("--nope"))
        assertEquals(Status.ERROR, options.status)
        assertTrue(options.error.contains("--nope"), options.error)
    }

    @Test
    @DisplayName("--help and -V stop parsing")
    fun helpAndVersion() {
        assertEquals(Status.HELP, Options.parse(arrayOf("--help")).status)
        assertEquals(Status.VERSION, Options.parse(arrayOf("-V")).status)
    }

    @Test
    @DisplayName("everything after -- is a file name, even if it looks like a flag")
    fun doubleDashStopsOptionParsing() {
        val options = Options.parse(arrayOf("--", "-l", "notes.txt"))
        assertEquals(Status.OK, options.status)
        assertEquals(listOf("-l", "notes.txt"), options.files)
    }

    @Test
    @DisplayName("- is accepted as the stdin placeholder")
    fun dashIsAFile() {
        assertEquals(listOf("-"), Options.parse(arrayOf("-")).files)
    }
}
