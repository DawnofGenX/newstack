package {{ package_name }}

import kotlin.system.exitProcess

/** Entry point: the only place that calls [exitProcess]. */
fun main(args: Array<String>) {
    exitProcess(Cli(System.`in`).run(args, System.out, System.err))
}
