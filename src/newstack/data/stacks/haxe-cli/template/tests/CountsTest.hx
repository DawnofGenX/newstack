package;

class CountsTest {
  static function bytes(text:String):haxe.io.Bytes {
    return haxe.io.Bytes.ofString(text);
  }

  public static function run():Void {
    var plain = TextStat.count(bytes("alpha beta\ngamma\n"));
    Harness.equal("two lines", plain.lines, 2);
    Harness.equal("three words", plain.words, 3);
    Harness.equal("bytes are the payload length", plain.bytes, 17);

    var noTrailing = TextStat.count(bytes("one two three"));
    Harness.equal("no trailing newline: lines", noTrailing.lines, 0);
    Harness.equal("no trailing newline: words", noTrailing.words, 3);
    Harness.equal("no trailing newline: bytes", noTrailing.bytes, 13);

    var empty = TextStat.count(bytes(""));
    Harness.equal("empty payload", '${empty.lines}/${empty.words}/${empty.bytes}', "0/0/0");

    var utf8 = TextStat.count(bytes("h\u00e9llo w\u00f6rld\n"));
    Harness.equal("utf-8 counts bytes, not characters", utf8.bytes, 14);
    Harness.equal("utf-8 words", utf8.words, 2);

    var controls = TextStat.count(bytes("a\tb\u000Bc\u000Cd\n"));
    Harness.equal("tab, vtab and form feed separate words", controls.words, 4);

    var spaces = TextStat.count(bytes("   "));
    Harness.equal("whitespace only has no words", spaces.words, 0);
    Harness.equal("whitespace only still has bytes", spaces.bytes, 3);

    var sum = TextStat.add(plain, noTrailing);
    Harness.equal("add sums every figure", '${sum.lines}/${sum.words}/${sum.bytes}', "2/6/30");
  }
}
