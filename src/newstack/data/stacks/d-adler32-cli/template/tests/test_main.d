module test_main;

import harness;
import counts_test;
import options_test;
import runner_test;

int main() {
    runCountsTests();
    runOptionsTests();
    runRunnerTests();
    Harness.finish();
    return 0;
}
