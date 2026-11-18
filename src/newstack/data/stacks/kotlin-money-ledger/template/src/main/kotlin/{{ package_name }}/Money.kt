package {{ package_name }}

// kotlin-money-ledger

import java.math.BigDecimal
import java.math.RoundingMode

/** An exact decimal amount in a single currency. Never use Double for money. */
data class Money(val amount: BigDecimal, val currency: String = "USD") {
    init {
        require(currency.length == 3) { "currency must be a 3 letter code: $currency" }
    }

    private fun sameCurrency(other: Money) {
        require(other.currency == currency) {
            "cannot combine $currency with ${other.currency}"
        }
    }

    operator fun plus(other: Money): Money {
        sameCurrency(other)
        return Money(amount.add(other.amount), currency)
    }

    operator fun minus(other: Money): Money {
        sameCurrency(other)
        return Money(amount.subtract(other.amount), currency)
    }

    operator fun times(factor: Int): Money = Money(amount.multiply(BigDecimal(factor)), currency)

    operator fun unaryMinus(): Money = Money(amount.negate(), currency)

    fun isZero(): Boolean = amount.signum() == 0

    fun format(): String = amount.setScale(2, RoundingMode.HALF_UP).toPlainString()

    companion object {
        val ZERO = Money(BigDecimal.ZERO)

        fun parse(text: String, currency: String = "USD"): Money =
            Money(BigDecimal(text.trim()), currency)
    }
}
