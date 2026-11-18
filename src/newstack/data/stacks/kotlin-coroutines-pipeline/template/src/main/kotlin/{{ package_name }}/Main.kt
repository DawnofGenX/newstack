package {{ package_name }}

import kotlinx.coroutines.runBlocking

fun main() = runBlocking {
    val result = Pipeline(4).run(10)
    println("pipeline result=$result")
}
