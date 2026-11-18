package {{ package_name }}

// kotlin-money-ledger

import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.assertThrows
import java.math.BigDecimal

class LedgerTest {
    private fun assertMoney(expected: String, actual: Money) {
        assertEquals(0, BigDecimal(expected).compareTo(actual.amount), "expected $expected got ${actual.format()}")
    }

    @Test
    fun postingAccumulatesPerAccount() {
        val ledger = Ledger()
        ledger.post("cash", Money.parse("100.00"))
        ledger.post("cash", Money.parse("-12.50"))
        assertMoney("87.50", ledger.balance("cash"))
        assertMoney("0", ledger.balance("missing"))
    }

    @Test
    fun trialBalanceIsZeroForDoubleEntry() {
        val ledger = Ledger()
        ledger.post("cash", Money.parse("-40.00"))
        ledger.post("inventory", Money.parse("40.00"))
        assertTrue(ledger.trialBalance().isZero(), "trial balance was ${ledger.trialBalance().format()}")
        assertMoney("0", ledger.trialBalance())
    }

    @Test
    fun reportIsSortedAndFormatted() {
        val ledger = Ledger()
        ledger.post("sales", Money.parse("12.5"))
        ledger.post("cash", Money.parse("7"))
        assertEquals(listOf("cash 7.00", "sales 12.50"), ledger.report())
    }

    @Test
    fun decimalsStayExact() {
        val ledger = Ledger()
        repeat(3) { ledger.post("fees", Money.parse("0.10")) }
        assertMoney("0.30", ledger.balance("fees"))
    }

    @Test
    fun mixedCurrenciesAreRejected() {
        val ledger = Ledger()
        ledger.post("cash", Money.parse("10.00", "USD"))
        assertThrows<IllegalArgumentException> { ledger.post("cash", Money.parse("5.00", "EUR")) }
    }

    @Test
    fun blankAccountIsRejected() {
        val ledger = Ledger()
        assertThrows<IllegalArgumentException> { ledger.post("  ", Money.parse("1")) }
    }

    @Test
    fun moneyArithmeticKeepsTheCurrency() {
        val total = Money.parse("10.00") + Money.parse("2.50") - Money.parse("0.50")
        assertMoney("12.00", total)
        assertEquals("USD", total.currency)
        assertMoney("-12.00", -total)
        assertMoney("24.00", total * 2)
    }
}
