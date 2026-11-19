module app;

import std.conv : to;
import std.format : format;
import std.stdio : stderr, stdout, write;
import floatbits;

int main(string[] argv) {
    immutable program = "{{ npm_name }}";

    if (argv.length < 2) {
        stderr.write("usage: " ~ program ~ " VALUE | bits HEX\n");
        return 2;
    }
    if (argv[1] == "--help" || argv[1] == "-h") {
        stdout.write("Usage: " ~ program ~ " VALUE\n");
        stdout.write("       " ~ program ~ " bits HEX\n");
        stdout.write("Inspect IEEE-754 double-precision bit patterns.\n");
        return 0;
    }
    if (argv[1] == "--version") {
        stdout.write(program ~ " 0.1.0\n");
        return 0;
    }
    if (argv[1] == "bits") {
        if (argv.length < 3) {
            stderr.write("missing hex value\n");
            return 2;
        }
        ulong raw;
        string hex = argv[2];
        if (hex.length > 2 && hex[0..2] == "0x") hex = hex[2..$];
        try {
            raw = to!ulong(hex, 16);
        } catch (Exception) {
            stderr.write("invalid hex: " ~ argv[2] ~ "\n");
            return 2;
        }
        stdout.write(to!string(fromBits(raw)) ~ "\n");
        return 0;
    }
    try {
        double value = to!double(argv[1]);
        stdout.write(formatBits(value) ~ "\n");
        return 0;
    } catch (Exception) {
        stderr.write("invalid number: " ~ argv[1] ~ "\n");
        return 2;
    }
}
