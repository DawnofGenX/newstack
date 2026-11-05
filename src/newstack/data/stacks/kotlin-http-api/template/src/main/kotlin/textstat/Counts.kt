package textstat

/**
 * Pure wc-style counting over RAW UTF-8 BYTES (never chars).
 *  - lines = number of 0x0A bytes
 *  - words = maximal runs of bytes NOT in {0x20,0x09,0x0A,0x0D,0x0B,0x0C}
 *  - bytes = array length
 */
object Counts {
    private val WORD_DELIMS: BooleanArray = BooleanArray(256).also { d ->
        for (b in intArrayOf(0x20, 0x09, 0x0A, 0x0D, 0x0B, 0x0C)) d[b] = true
    }

    /** true if byte b (as unsigned) is a word delimiter */
    fun isDelim(b: Int): Boolean = WORD_DELIMS[b and 0xFF]

    fun lines(bytes: ByteArray): Int {
        var n = 0
        for (b in bytes) if (b == 0x0A.toByte()) n++
        return n
    }

    fun words(bytes: ByteArray): Int {
        var n = 0
        var inWord = false
        for (b in bytes) {
            val d = isDelim(b.toInt())
            if (!inWord && !d) { n++; inWord = true }
            else if (d) inWord = false
        }
        return n
    }

    fun bytes(bytes: ByteArray): Int = bytes.size
}
