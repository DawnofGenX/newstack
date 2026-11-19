module floatbits;

import std.format : format;

struct Bits {
    ulong raw;
    bool sign;
    uint exponent;
    ulong mantissa;
}

Bits inspect(double value) {
    union Caster { double d; ulong u; }
    Caster c;
    c.d = value;
    Bits b;
    b.raw = c.u;
    b.sign = (c.u >> 63) != 0;
    b.exponent = cast(uint) ((c.u >> 52) & 0x7ff);
    b.mantissa = c.u & ((1UL << 52) - 1);
    return b;
}

double fromBits(ulong raw) {
    union Caster { double d; ulong u; }
    Caster c;
    c.u = raw;
    return c.d;
}

string formatBits(double value) {
    auto b = inspect(value);
    return format("sign=%d exponent=%d mantissa=%d hex=0x%016x",
        b.sign ? 1 : 0, b.exponent, b.mantissa, b.raw);
}

unittest {
    auto b = inspect(1.0);
    assert(b.raw == 0x3ff0000000000000UL);
    assert(b.sign == false);
    assert(b.exponent == 1023);
    assert(b.mantissa == 0);
    assert(fromBits(0x400921fb54442d18UL) == 3.141592653589793);
}
