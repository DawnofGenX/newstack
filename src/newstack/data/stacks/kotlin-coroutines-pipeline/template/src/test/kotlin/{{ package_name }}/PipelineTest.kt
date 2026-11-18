package {{ package_name }}

import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.flow.toList
import kotlinx.coroutines.flow.asFlow
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Test

class PipelineTest {
    @Test
    fun runProducesExpectedSum() = runTest {
        // source 1..4: value*2 then +1 => 3,5,7,9 sum=24
        assertEquals(24, Pipeline(2).run(4))
    }

    @Test
    fun fanOutPreservesAllItems() = runTest {
        val out = Pipeline(3).fanOut(
            Pipeline(3).transform(FakeSource(5).produce())
        ).toList()
        assertEquals(5, out.size)
    }

    @Test
    fun fanInSums() = runTest {
        val sum = Pipeline(1).fanIn(listOf(1, 2, 3).asFlow())
        assertEquals(6, sum)
    }
}
