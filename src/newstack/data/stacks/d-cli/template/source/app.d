/// The only file that touches the real process.
module app;

import std.file : read;
import std.stdio : stderr, stdout, write;

import runner;

ubyte[] readFile(string path) {
    return cast(ubyte[]) read(path);
}

ubyte[] readStdin() {
    return cast(ubyte[]) read("/dev/stdin");
}

int main(string[] argv) {
    immutable program = "{{ npm_name }}";
    auto io = Io(&readFile, &readStdin);
    auto report = run(program, argv[1 .. $], io);
    stdout.write(report.outText);
    stderr.write(report.errText);
    return report.code;
}
