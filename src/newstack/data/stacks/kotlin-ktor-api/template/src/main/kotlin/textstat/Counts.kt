package textstat

/**
 * wc(1) semantics applied to raw UTF-8 bytes.
 *
 * lines = count of 0x0A bytes
 * words = maximal runs of bytes outside the wc separator set
 * bytes = length of the UTF-8 encoding
 */
object Counts {
    val WORD_SEPARATORS: Set<Byte> = setOf(0x20, 0x09, 0x0A, 0x0D, 0x0B, 0x0C)

    fun lines(bytes: ByteArray): Int {
        var n = 0
        for (b in bytes) if (b == 0x0A.toByte()) n++
        return n
    }

    fun words(bytes: ByteArray): Int {
        var n = 0
        var inWord = false
        for (b in bytes) {
            if (b in WORD_SEPARATORS) {
                inWord = false
            } else if (!inWord) {
                inWord = true
                n++
            }
        }
        return n
    }

    fun bytes(text: String): ByteArray = text.toByteArray(Charsets.UTF_8)

    fun lines(text: String): Int = lines(bytes(text))
    fun words(text: String): Int = words(bytes(text))
    fun byteCount(text: String): Int = bytes(text).size
}
