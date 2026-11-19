/// Report building over an Io struct, so the tests can fake the disk.
module runner;

import std.array : appender;
import std.conv : to;
import std.format : format;

import options;
import textstat;

struct Io {
    ubyte[] function(string path) readFile;
    ubyte[] function() readStdin;
}

struct Report {
    string outText;
    string errText;
    int code;
}

private struct Reading {
    string label;
    Counts counts;
}

private size_t digits(size_t value) {
    return value.to!string.length;
}

private size_t figureWidth(size_t operands, size_t figures, Counts total, bool hasStream) {
    if (operands == 1 && figures == 1) return 0;
    if (hasStream) return 7;
    return digits(total.bytes);
}

private size_t figureCount(Options options) {
    size_t figures = 0;
    if (options.lines) figures++;
    if (options.words) figures++;
    if (options.bytes) figures++;
    return figures;
}

private string padTo(size_t width, string text) {
    if (text.length >= width) return text;
    return format("%*s", cast(int) width, text);
}

private string row(Options options, Counts counts, size_t width, string label) {
    string[] cells;
    if (options.lines) cells ~= counts.lines.to!string;
    if (options.words) cells ~= counts.words.to!string;
    if (options.bytes) cells ~= counts.bytes.to!string;

    string[] padded;
    foreach (cell; cells) padded ~= padTo(width, cell);

    auto text = appender!string();
    foreach (i, cell; padded) {
        if (i > 0) text.put(" ");
        text.put(cell);
    }
    if (label.length > 0) {
        text.put(" ");
        text.put(label);
    }
    text.put("\n");
    return text.data;
}

Report run(string program, string[] argv, Io io) {
    auto parsed = parse(argv);

    final switch (parsed.status) {
    case Status.help:
        return Report(usage(program), "", 0);
    case Status.version_:
        return Report(program ~ " " ~ toolVersion ~ "\n", "", 0);
    case Status.usageError:
        return Report("", program ~ ": " ~ parsed.message ~ "\n" ~ usage(program), 2);
    case Status.ok:
        break;
    }

    auto options = parsed.options;
    bool implicitInput = options.operands.length == 0;
    string[] operands = implicitInput ? ["-"] : options.operands;

    bool hasStream = implicitInput;
    foreach (operand; operands) {
        if (operand == "-") hasStream = true;
    }

    Reading[] readings;
    string errorText;
    bool failed = false;

    foreach (operand; operands) {
        ubyte[] payload;
        try {
            payload = operand == "-" ? io.readStdin() : io.readFile(operand);
        } catch (Exception error) {
            failed = true;
            errorText ~= program ~ ": " ~ operand ~ ": No such file or directory\n";
            continue;
        }
        readings ~= Reading(implicitInput ? "" : operand, count(payload));
    }

    Counts total;
    foreach (reading; readings) total = add(total, reading.counts);

    auto width = figureWidth(operands.length, figureCount(options), total, hasStream);

    auto outText = appender!string();
    foreach (reading; readings) {
        outText.put(row(options, reading.counts, width, reading.label));
    }
    if (operands.length > 1) {
        outText.put(row(options, total, width, "total"));
    }

    return Report(outText.data, errorText, failed ? 1 : 0);
}
