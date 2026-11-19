module test_main;

import harness;
import floatbits_test;

int main() {
    runFloatBitsTests();
    Harness.finish();
    return 0;
}
