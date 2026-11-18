package {{ package_name }}

/** Double entry ledger keyed by account name. Debits are negative amounts. */
class Ledger {
    private val balances = LinkedHashMap<String, Money>()

    fun post(account: String, amount: Money): Money {
        require(account.isNotBlank()) { "account must not be blank" }
        val current = balances[account] ?: Money.ZERO
        val updated = current + amount
        balances[account] = updated
        return updated
    }

    fun balance(account: String): Money = balances[account] ?: Money.ZERO

    /** Account names in insertion order, sorted for stable report output. */
    fun accounts(): List<String> = balances.keys.sorted()

    /** The sum of every account; a balanced ledger always totals zero. */
    fun trialBalance(): Money = balances.values.fold(Money.ZERO) { total, money -> total + money }

    fun report(): List<String> = accounts().map { "$it ${balance(it).format()}" }
}
