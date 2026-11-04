import harness
import textstat/runner

/// Run the runner tests. Returns a list of failed check names (empty if all
/// pass).
///
/// These assert the exit-code contract without spawning a process: `run`
/// returns the code that `main` hands to `erlang:halt`.
pub fn run() -> List(String) {
  [
    // --help exits 0.
    harness.check_eq("help exits 0", runner.run(["--help"], <<>>), 0),
    // -V exits 0.
    harness.check_eq("version exits 0", runner.run(["-V"], <<>>), 0),
    // Unknown flag exits 2.
    harness.check_eq("usage error exits 2", runner.run(["--bogus"], <<>>), 2),
    // No files: read stdin, exit 0.
    harness.check_eq("stdin exits 0", runner.run([], <<"hello\n">>), 0),
    // "-" names stdin, exit 0.
    harness.check_eq("dash stdin exits 0", runner.run(["-"], <<"hello\n">>), 0),
    // Missing file exits 1.
    harness.check_eq(
      "missing file exits 1",
      runner.run(["does-not-exist-xyz-12345.txt"], <<>>),
      1,
    ),
  ]
}
