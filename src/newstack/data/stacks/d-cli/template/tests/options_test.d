module options_test;

import std.array : join;

import harness;
import options;

void runOptionsTests() {
    auto defaults = parse([]);
    Harness.check("no flags means all three figures",
        defaults.status == Status.ok && defaults.options.lines
        && defaults.options.words && defaults.options.bytes);

    auto cluster = parse(["-lw"]);
    Harness.check("clustered flags apply both",
        cluster.options.lines && cluster.options.words && !cluster.options.bytes);

    auto longForm = parse(["--bytes"]);
    Harness.check("long flag", longForm.options.bytes && !longForm.options.lines);

    auto dash = parse(["-", "b.txt"]);
    Harness.equal("dash stays an operand", dash.options.operands.join(","), "-,b.txt");

    auto terminator = parse(["--", "-l"]);
    Harness.equal("-- stops option parsing", terminator.options.operands.join(","), "-l");

    Harness.check("--help asks for help", parse(["--help"]).status == Status.help);
    Harness.check("-h asks for help", parse(["-h"]).status == Status.help);
    Harness.check("--version asks for the version", parse(["--version"]).status == Status.version_);

    auto unknownLong = parse(["--bogus"]);
    Harness.check("unknown long option is a usage error", unknownLong.status == Status.usageError);

    auto unknownShort = parse(["-z"]);
    Harness.check("unknown short option is a usage error", unknownShort.status == Status.usageError);
}
