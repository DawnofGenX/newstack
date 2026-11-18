package {{ package_name }}

/** RFC 4648 base32 with padding, strict on decode. */
object Base32 {
    private const val ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"
    private val INDEX: Map<Char, Int> = ALPHABET.withIndex().associate { (index, char) -> char to index }

    class Base32Exception(message: String) : Exception(message)

    fun encode(input: ByteArray): String {
        val builder = StringBuilder()
        var buffer = 0
        var bits = 0
        for (byte in input) {
            buffer = (buffer shl 8) or (byte.toInt() and 0xFF)
            bits += 8
            while (bits >= 5) {
                bits -= 5
                builder.append(ALPHABET[(buffer shr bits) and 0x1F])
            }
        }
        if (bits > 0) {
            builder.append(ALPHABET[(buffer shl (5 - bits)) and 0x1F])
        }
        while (builder.length % 8 != 0) {
            builder.append('=')
        }
        return builder.toString()
    }

    fun decode(text: String): ByteArray {
        val cleaned = text.filterNot { it.isWhitespace() }.trimEnd('=')
        if (cleaned.isEmpty()) {
            if (text.any { it != '=' && !it.isWhitespace() }) {
                throw Base32Exception("invalid base32 input: ${text.trim()}")
            }
            return ByteArray(0)
        }
        when (cleaned.length % 8) {
            1, 3, 6 -> throw Base32Exception("truncated base32 input: ${cleaned.length} characters is not a valid group length")
            else -> Unit
        }
        val output = ArrayList<Byte>(cleaned.length * 5 / 8)
        var buffer = 0
        var bits = 0
        for (raw in cleaned) {
            val char = raw.uppercaseChar()
            val value = INDEX[char]
                ?: throw Base32Exception("invalid base32 character '$raw'")
            buffer = (buffer shl 5) or value
            bits += 5
            if (bits >= 8) {
                bits -= 8
                output.add(((buffer shr bits) and 0xFF).toByte())
            }
        }
        if ((buffer and ((1 shl bits) - 1)) != 0) {
            throw Base32Exception("non-zero padding bits in the last base32 character")
        }
        return output.toByteArray()
    }
}
