// The program: hand the real IO to the runner and exit with its code.

import { systemIO } from "./src/io.ts";
import { run } from "./src/runner.ts";

Deno.exit(run(Deno.args, systemIO(), "{{ npm_name }}"));
