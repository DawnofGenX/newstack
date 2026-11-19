module floatbits_test;

import floatbits;
import harness;

void runFloatBitsTests() {
    auto b = inspect(1.0);
    Harness.check("one bits raw", b.raw == 0x3ff0000000000000UL);
    Harness.check("one bits exponent", b.exponent == 1023);
    Harness.check("from bits pi", fromBits(0x400921fb54442d18UL) == 3.141592653589793);
    Harness.equal("format bits", formatBits(1.0), "sign=0 exponent=1023 mantissa=0 hex=0x3ff0000000000000");
}

unittest {
    runFloatBitsTests();
}
