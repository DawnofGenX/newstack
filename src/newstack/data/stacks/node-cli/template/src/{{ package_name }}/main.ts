import { main } from "./cli.js";

/**
 * `prog | head -1` closes the pipe while we are still writing. Node reports that as
 * an unhandled 'error' event on stdout, prints a stack trace and exits 1, so every
 * pipeline that truncates our output looks like a crash. Silently succeeding is the
 * correct behaviour: the reader asked for one line and got it.
 */
process.stdout.on("error", (error: NodeJS.ErrnoException) => {
  if (error.code === "EPIPE") {
    process.exit(0);
  }
  throw error;
});

process.exitCode = await main(process.argv.slice(2));
