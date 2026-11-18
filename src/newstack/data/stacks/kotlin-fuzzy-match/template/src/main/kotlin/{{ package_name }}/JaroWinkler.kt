package {{ package_name }}

/**
 * Jaro and Jaro-Winkler string similarity, the classic record-linkage measure.
 *
 * Jaro compares two strings in a window of `max(len) / 2 - 1` characters and counts
 * transpositions among the matched characters. Winkler then boosts the score for strings that
 * share a prefix, which is what makes it good at catching "JOHN" vs "JON" style typos.
 */
object JaroWinkler {
    fun jaro(left: String, right: String): Double {
        if (left == right) return 1.0
        if (left.isEmpty() || right.isEmpty()) return 0.0

        val window = maxOf(left.length, right.length) / 2 - 1
        val leftMatched = BooleanArray(left.length)
        val rightMatched = BooleanArray(right.length)
        var matches = 0

        for (index in left.indices) {
            val start = maxOf(0, index - window)
            val end = minOf(right.length - 1, index + window)
            for (candidate in start..end) {
                if (rightMatched[candidate] || right[candidate] != left[index]) continue
                leftMatched[index] = true
                rightMatched[candidate] = true
                matches += 1
                break
            }
        }
        if (matches == 0) return 0.0

        var transpositions = 0
        var cursor = 0
        for (index in left.indices) {
            if (!leftMatched[index]) continue
            while (!rightMatched[cursor]) cursor += 1
            if (left[index] != right[cursor]) transpositions += 1
            cursor += 1
        }

        val half = transpositions / 2.0
        val m = matches.toDouble()
        return (m / left.length + m / right.length + (m - half) / m) / 3.0
    }

    fun winkler(
        left: String,
        right: String,
        prefixScale: Double = 0.1,
        maxPrefix: Int = 4,
    ): Double {
        val base = jaro(left, right)
        if (base <= 0.0) return base
        var prefix = 0
        while (prefix < minOf(maxPrefix, left.length, right.length) && left[prefix] == right[prefix]) {
            prefix += 1
        }
        return base + prefix * prefixScale * (1.0 - base)
    }

    /** The highest scoring candidate, or null for an empty list. */
    fun best(target: String, candidates: List<String>): Pair<String, Double>? =
        candidates
            .map { it to winkler(target, it) }
            .maxByOrNull { it.second }

    /** Candidates ordered by descending similarity. */
    fun rank(target: String, candidates: List<String>): List<Pair<String, Double>> =
        candidates.map { it to winkler(target, it) }.sortedByDescending { it.second }
}
