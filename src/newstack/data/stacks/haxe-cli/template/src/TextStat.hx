package;

typedef Counts = {
  var lines:Int;
  var words:Int;
  var bytes:Int;
}

/**
  Counts a byte payload exactly the way wc(1) does: lines are 0x0A bytes,
  words are maximal runs of non-whitespace bytes, bytes is the payload length.
**/
class TextStat {
  static inline function isSpace(b:Int):Bool {
    return b == 32 || b == 9 || b == 10 || b == 13 || b == 11 || b == 12;
  }

  public static function count(bytes:haxe.io.Bytes):Counts {
    var lines = 0;
    var words = 0;
    var inWord = false;
    for (i in 0...bytes.length) {
      var b = bytes.get(i);
      if (b == 10) lines++;
      if (isSpace(b)) {
        inWord = false;
      } else if (!inWord) {
        inWord = true;
        words++;
      }
    }
    return {lines: lines, words: words, bytes: bytes.length};
  }

  public static function add(left:Counts, right:Counts):Counts {
    return {
      lines: left.lines + right.lines,
      words: left.words + right.words,
      bytes: left.bytes + right.bytes
    };
  }
}
