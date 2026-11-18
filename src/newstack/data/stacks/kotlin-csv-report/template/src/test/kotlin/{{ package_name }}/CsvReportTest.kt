package {{ package_name }}

import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.assertThrows
import org.junit.jupiter.api.Test

class CsvReportTest {
    private val sample = "name,dept,score\nalice,eng,10\nbob,eng,20\ncarol,sales,5\n"

    @Test
    fun parsesRowsAndHeaders() {
        val t = Csv.parse(sample)
        assertEquals(listOf("name", "dept", "score"), t.headers)
        assertEquals(3, t.rows.size)
    }

    @Test
    fun groupCount() {
        val t = Csv.parse(sample)
        assertEquals(mapOf("eng" to 2, "sales" to 1), Report.groupCount(t, "dept"))
    }

    @Test
    fun sumColumn() {
        val t = Csv.parse(sample)
        assertEquals(35.0, Report.sum(t, "score"))
    }

    @Test
    fun quotedFields() {
        val t = Csv.parse("a,b\n\"x,y\",2\n")
        assertEquals(listOf("x,y", "2"), t.rows.first())
    }

    @Test
    fun emptyInputHasNoHeaders() {
        val t = Csv.parse("")
        assertEquals(emptyList<String>(), t.headers)
        assertEquals(0, t.rows.size)
    }

    @Test
    fun unknownColumnIsRejected() {
        val t = Csv.parse(sample)
        val err = assertThrows<IllegalArgumentException> { Report.groupCount(t, "missing") }
        assertEquals("unknown column: missing", err.message)
    }
}
