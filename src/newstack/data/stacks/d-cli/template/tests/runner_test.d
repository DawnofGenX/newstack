module runner_test;

import std.algorithm.searching : canFind;

import harness;
import runner;

private string stdinText = "";

ubyte[] fakeFile(string path) {
    if (path == "a.txt") return cast(ubyte[]) "alpha beta\ngamma delta\n";
    if (path == "b.txt") return cast(ubyte[]) "one two three";
    throw new Exception("missing: " ~ path);
}

ubyte[] fakeStdin() {
    return cast(ubyte[]) stdinText;
}

private Report report(string[] argv, string stdinPayload) {
    stdinText = stdinPayload;
    auto io = Io(&fakeFile, &fakeStdin);
    return run("textstat", argv, io);
}

void runRunnerTests() {
    auto single = report(["a.txt"], "");
    Harness.equal("one file, one row", single.outText, " 2  4 23 a.txt\n");
    Harness.equalInt("one file exits 0", single.code, 0);

    auto pair = report(["a.txt", "b.txt"], "");
    Harness.equal("two files get a total row", pair.outText,
        " 2  4 23 a.txt\n 0  3 13 b.txt\n 2  7 36 total\n");

    auto narrow = report(["-w", "a.txt", "b.txt"], "");
    Harness.equal("-w pads to the byte total's width", narrow.outText,
        " 4 a.txt\n 3 b.txt\n 7 total\n");

    auto fromStdin = report([], "alpha beta\ngamma\n");
    Harness.equal("stdin row is unlabelled", fromStdin.outText, "      2       3      17\n");

    auto dash = report(["-"], "x y\n");
    Harness.equal("explicit dash is labelled", dash.outText, "      1       2       4 -\n");

    auto mixed = report(["a.txt", "-"], "x y\n");
    Harness.equal("a pipeline operand forces seven columns", mixed.outText,
        "      2       4      23 a.txt\n      1       2       4 -\n"
        ~ "      3       6      27 total\n");

    auto missing = report(["a.txt", "gone.txt"], "");
    Harness.equalInt("a missing file exits 1", missing.code, 1);
    Harness.equal("the readable file is still counted", missing.outText,
        " 2  4 23 a.txt\n 2  4 23 total\n");
    Harness.check("the error names the file", missing.errText.canFind("gone.txt"));

    auto help = report(["--help"], "");
    Harness.check("help exits 0", help.code == 0);
    Harness.check("help goes to stdout", help.outText.length > 0 && help.outText[0 .. 13] == "Usage: textst");
    Harness.equal("help writes nothing to stderr", help.errText, "");

    auto versioned = report(["--version"], "");
    Harness.equal("version is one line", versioned.outText, "textstat 0.1.0\n");

    auto usageError = report(["--nope"], "");
    Harness.equalInt("usage errors exit 2", usageError.code, 2);
    Harness.equal("usage errors write nothing to stdout", usageError.outText, "");
}
