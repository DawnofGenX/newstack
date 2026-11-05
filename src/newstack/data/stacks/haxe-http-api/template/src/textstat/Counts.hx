package textstat;

/**
 * Counts the way `wc` does: a line is one '\n', a word is a maximal run of
 * non-space bytes, and bytes are the UTF-8 length. Counting walks the UTF-8
 * bytes rather than the Haxe string, so a string with accents or emoji reports
 * the size it will actually occupy on the wire.
 */
class Counts {
	public var lines:Int;
	public var words:Int;
	public var bytes:Int;

	public function new(lines:Int, words:Int, bytes:Int) {
		this.lines = lines;
		this.words = words;
		this.bytes = bytes;
	}

	public static function of(text:String):Counts {
		var lines = 0;
		var words = 0;
		var inWord = false;
		var data = haxe.io.Bytes.ofString(text);
		for (index in 0...data.length) {
			var byte = data.get(index);
			if (byte == 10) {
				lines += 1;
			}
			if (isSpace(byte)) {
				inWord = false;
			} else if (!inWord) {
				inWord = true;
				words += 1;
			}
		}
		return new Counts(lines, words, data.length);
	}

	static function isSpace(byte:Int):Bool {
		return byte == 32 || byte == 9 || byte == 10 || byte == 13 || byte == 11 || byte == 12;
	}

	public function toString():String {
		return 'Counts($lines, $words, $bytes)';
	}
}
