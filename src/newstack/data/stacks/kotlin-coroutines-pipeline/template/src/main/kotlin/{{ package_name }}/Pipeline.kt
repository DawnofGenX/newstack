package {{ package_name }}

import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*

data class Item(val id: Int, val value: Int)

class FakeSource(private val count: Int) {
    fun produce(): Flow<Item> = (1..count).asFlow().map { Item(it, it) }
}

class Pipeline(private val concurrency: Int = 4) {
    fun transform(input: Flow<Item>): Flow<Int> = input.map { it.value * 2 }

    fun fanOut(input: Flow<Int>): Flow<Int> = input.flatMapMerge(concurrency) { value ->
        flow {
            delay(1) // simulated staged work
            emit(value + 1)
        }
    }

    suspend fun fanIn(input: Flow<Int>): Int = input.fold(0) { acc, v -> acc + v }

    suspend fun run(count: Int): Int {
        val source = FakeSource(count).produce()
        val transformed = transform(source)
        val fanned = fanOut(transformed)
        return fanIn(fanned)
    }
}
