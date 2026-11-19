/// A test harness small enough to read: counters, three assertions, a summary.
module harness;

import core.stdc.stdlib : exit;
import std.conv : to;
import std.stdio : writeln;

struct Harness {
    static size_t passed;
    static size_t failed;

    static void check(string label, bool condition) {
        if (condition) {
            passed++;
            writeln("ok   ", label);
        } else {
            failed++;
            writeln("FAIL ", label);
        }
    }

    static void equal(string label, string got, string want) {
        auto ok = got == want;
        check(ok ? label : label ~ " (got [" ~ got ~ "], want [" ~ want ~ "])", ok);
    }

    static void equalInt(string label, size_t got, size_t want) {
        equal(label, got.to!string, want.to!string);
    }

    static void finish() {
        writeln();
        writeln("checks: ", passed + failed, ", passed: ", passed, ", failed: ", failed);
        if (failed != 0) exit(1);
    }
}
