package {{ package_name }}

import kotlin.test.Test
import kotlin.test.assertContentEquals
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith

class Base32Test {
    @Test
    fun encodesTheRfc4648Vectors() {
        val cases = listOf(
            "" to "",
            "f" to "MY======",
            "fo" to "MZXQ====",
            "foo" to "MZXW6===",
            "foob" to "MZXW6YQ=",
            "fooba" to "MZXW6YTB",
            "foobar" to "MZXW6YTBOI======",
        )
        for ((plain, encoded) in cases) {
            assertEquals(encoded, Base32.encode(plain.toByteArray()), plain)
            assertContentEquals(plain.toByteArray(), Base32.decode(encoded), encoded)
        }
    }

    @Test
    fun roundTripsBinaryPayloads() {
        val payload = ByteArray(37) { (it * 7 + 3).toByte() }
        assertContentEquals(payload, Base32.decode(Base32.encode(payload)))
    }

    @Test
    fun acceptsLowercaseAndUnpaddedInput() {
        assertEquals("foobar", String(Base32.decode("mzxw6ytboi")))
        assertEquals("foobar", String(Base32.decode("MZXW6YTBOI======")))
    }

    @Test
    fun ignoresWhitespace() {
        assertEquals("foobar", String(Base32.decode("MZXW 6YTB OI======")))
    }

    @Test
    fun rejectsInvalidCharacters() {
        val error = assertFailsWith<Base32.Base32Exception> { Base32.decode("MZXW1===") }
        assertEquals("invalid base32 character '1'", error.message)
    }

    @Test
    fun rejectsTruncatedGroups() {
        for (text in listOf("M", "MZX", "MZXW6Y")) {
            assertFailsWith<Base32.Base32Exception>(text) { Base32.decode(text) }
        }
    }

    @Test
    fun rejectsNonZeroPaddingBits() {
        val error = assertFailsWith<Base32.Base32Exception> { Base32.decode("MZ======") }
        assertEquals("non-zero padding bits in the last base32 character", error.message)
    }

    @Test
    fun cliEncodesAndDecodes() {
        val out = StringBuilder()
        assertEquals(0, run(listOf("encode", "foobar"), { "" }, { out.appendLine(it) }, { }))
        assertEquals("MZXW6YTBOI======", out.toString().trim())
        val back = StringBuilder()
        assertEquals(0, run(listOf("decode", "MZXW6YTBOI======"), { "" }, { back.appendLine(it) }, { }))
        assertEquals("foobar", back.toString().trim())
    }

    @Test
    fun cliReadsStdinAndHex() {
        val out = StringBuilder()
        assertEquals(0, run(listOf("encode", "--hex"), { "68656c6c6f" }, { out.appendLine(it) }, { }))
        assertEquals("NBSWY3DP", out.toString().trim())
        val back = StringBuilder()
        assertEquals(0, run(listOf("decode", "--hex"), { "NBSWY3DP" }, { back.appendLine(it) }, { }))
        assertEquals("68656c6c6f", back.toString().trim())
    }

    @Test
    fun cliRejectsBadUsageAndBadPayloads() {
        assertEquals(2, run(emptyList(), { "" }, { }, { }))
        assertEquals(2, run(listOf("frobnicate"), { "" }, { }, { }))
        assertEquals(2, run(listOf("encode", "--file"), { "" }, { }, { }))
        assertEquals(1, run(listOf("decode", "MZXW1==="), { "" }, { }, { }))
    }
}
