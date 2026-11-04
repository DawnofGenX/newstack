package;

import Runner.Io;

class FakeIo implements Io {
  public var files:Map<String, haxe.io.Bytes>;
  public var stdin:Null<haxe.io.Bytes>;
  public var asked:Array<String> = [];

  public function new(files:Map<String, haxe.io.Bytes>, ?stdin:haxe.io.Bytes) {
    this.files = files;
    this.stdin = stdin;
  }

  public function readFileBytes(path:String):haxe.io.Bytes {
    asked.push(path);
    if (!files.exists(path)) throw 'missing: $path';
    return files.get(path);
  }

  public function readStdinBytes():haxe.io.Bytes {
    asked.push("-");
    return stdin == null ? haxe.io.Bytes.alloc(0) : stdin;
  }
}

class RunnerTest {
  static function bytes(text:String):haxe.io.Bytes {
    return haxe.io.Bytes.ofString(text);
  }

  static function files():Map<String, haxe.io.Bytes> {
    var map = new Map<String, haxe.io.Bytes>();
    map.set("a.txt", bytes("alpha beta\ngamma delta\n"));
    map.set("b.txt", bytes("one two three"));
    return map;
  }

  static function run(program:String, args:Array<String>, io:FakeIo):{out:String, err:String, code:Int} {
    var out = new StringBuf();
    var err = new StringBuf();
    var code = Runner.run(program, args, io, out, err);
    return {out: out.toString(), err: err.toString(), code: code};
  }

  public static function runTests():Void {
    var plain = run("textstat", ["a.txt"], new FakeIo(files()));
    Harness.equal("one file, one row", plain.out, " 2  4 23 a.txt\n");
    Harness.equal("one file exits 0", plain.code, 0);

    var total = run("textstat", ["a.txt", "b.txt"], new FakeIo(files()));
    Harness.equal("two files get a total row", total.out, " 2  4 23 a.txt\n 0  3 13 b.txt\n 2  7 36 total\n");

    var narrow = run("textstat", ["-w", "a.txt", "b.txt"], new FakeIo(files()));
    Harness.equal("-w pads to the byte total's width", narrow.out, " 4 a.txt\n 3 b.txt\n 7 total\n");

    var stdinRun = run("textstat", [], new FakeIo(files(), bytes("alpha beta\ngamma\n")));
    Harness.equal("stdin row is unlabelled", stdinRun.out, "      2       3      17\n");

    var explicitDash = run("textstat", ["-"], new FakeIo(files(), bytes("x y\n")));
    Harness.equal("explicit dash is labelled", explicitDash.out, "      1       2       4 -\n");

    var mixed = run("textstat", ["a.txt", "-"], new FakeIo(files(), bytes("x y\n")));
    Harness.equal("a pipeline operand forces seven columns", mixed.out,
      "      2       4      23 a.txt\n      1       2       4 -\n      3       6      27 total\n");

    var missing = run("textstat", ["a.txt", "gone.txt"], new FakeIo(files()));
    Harness.equal("a missing file exits 1", missing.code, 1);
    Harness.equal("the readable file is still counted", missing.out, " 2  4 23 a.txt\n 2  4 23 total\n");
    Harness.check("the error names the file", missing.err.indexOf("gone.txt") >= 0);

    var allMissing = run("textstat", ["gone.txt", "lost.txt"], new FakeIo(files()));
    Harness.equal("all missing still prints a total", allMissing.out, "0 0 0 total\n");
    Harness.equal("all missing exits 1", allMissing.code, 1);

    var help = run("textstat", ["--help"], new FakeIo(files()));
    Harness.check("help goes to stdout and exits 0", help.code == 0 && help.out.indexOf("Usage: textstat") == 0);
    Harness.equal("help writes nothing to stderr", help.err, "");

    var version = run("textstat", ["--version"], new FakeIo(files()));
    Harness.equal("version is one line", version.out, "textstat 0.1.0\n");

    var usage = run("textstat", ["--nope"], new FakeIo(files()));
    Harness.equal("usage errors exit 2", usage.code, 2);
    Harness.equal("usage errors write nothing to stdout", usage.out, "");
    Harness.check("usage errors explain themselves", usage.err.indexOf("--nope") >= 0);
  }
}
