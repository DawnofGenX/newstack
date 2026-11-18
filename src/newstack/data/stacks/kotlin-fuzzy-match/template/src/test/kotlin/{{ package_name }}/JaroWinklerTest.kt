package {{ package_name }}

import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertNull
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.Test

class JaroWinklerTest {
    private val tolerance = 1e-6

    @Test
    fun identicalStringsScoreOne() {
        assertEquals(1.0, JaroWinkler.jaro("hello", "hello"), tolerance)
        assertEquals(1.0, JaroWinkler.winkler("hello", "hello"), tolerance)
    }

    @Test
    fun nothingInCommonScoresZero() {
        assertEquals(0.0, JaroWinkler.jaro("abc", "xyz"), tolerance)
        assertEquals(0.0, JaroWinkler.winkler("abc", "xyz"), tolerance)
    }

    @Test
    fun emptyInputIsOnlySimilarToEmptyInput() {
        assertEquals(1.0, JaroWinkler.jaro("", ""), tolerance)
        assertEquals(0.0, JaroWinkler.jaro("", "abc"), tolerance)
        assertEquals(0.0, JaroWinkler.winkler("abc", ""), tolerance)
    }

    @Test
    fun knownValuesFromTheLiterature() {
        // The examples every Jaro-Winkler description uses.
        assertEquals(0.944444, JaroWinkler.jaro("MARTHA", "MARHTA"), tolerance)
        assertEquals(0.961111, JaroWinkler.winkler("MARTHA", "MARHTA"), tolerance)
        assertEquals(0.766667, JaroWinkler.jaro("DIXON", "DICKSONX"), tolerance)
        assertEquals(0.813333, JaroWinkler.winkler("DIXON", "DICKSONX"), tolerance)
        assertEquals(0.733333, JaroWinkler.jaro("CRATE", "TRACE"), tolerance)
        // No shared prefix, so the Winkler boost is exactly zero.
        assertEquals(JaroWinkler.jaro("CRATE", "TRACE"), JaroWinkler.winkler("CRATE", "TRACE"), tolerance)
    }

    @Test
    fun theScoreIsSymmetric() {
        assertEquals(JaroWinkler.winkler("MARTHA", "MARHTA"), JaroWinkler.winkler("MARHTA", "MARTHA"), tolerance)
    }

    @Test
    fun thePrefixBoostIsCappedAtFourCharacters() {
        val base = JaroWinkler.jaro("abcdef", "abcdefg")
        val boosted = JaroWinkler.winkler("abcdef", "abcdefg")
        assertEquals(base + 4 * 0.1 * (1.0 - base), boosted, tolerance)
    }

    @Test
    fun thePrefixBoostCanBeDisabled() {
        assertEquals(
            JaroWinkler.jaro("MARTHA", "MARHTA"),
            JaroWinkler.winkler("MARTHA", "MARHTA", prefixScale = 0.0),
            tolerance,
        )
    }

    @Test
    fun bestPicksTheClosestCandidate() {
        val winner = JaroWinkler.best("recieve", listOf("receive", "relieve", "believe"))
        assertEquals("receive", winner?.first)
        assertTrue((winner?.second ?: 0.0) > 0.9)
    }

    @Test
    fun bestOfNothingIsNull() {
        assertNull(JaroWinkler.best("anything", emptyList()))
    }

    @Test
    fun rankIsOrderedByScore() {
        val ranked = JaroWinkler.rank("colour", listOf("color", "collar", "caterpillar"))
        assertEquals("color", ranked.first().first)
        assertEquals(listOf("color", "collar", "caterpillar"), ranked.map { it.first })
    }
}
