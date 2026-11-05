package textstat;

/**
 * What a POST body turned out to be. `haxe.Json` loses the difference between a
 * JSON string and a JSON number at runtime, so the body is re-read by hand:
 * only a quoted value counts as text.
 */
class JsonBody {
	/** Returns the `text` member of a JSON object, or why there is none. */
	public static function read(body:String):TextKind {
		var trimmed = StringTools.trim(body);
		if (trimmed.length == 0 || trimmed.charAt(0) != "{") {
			return Invalid;
		}
		// Validate the document first: haxe.Json.parse throws on anything malformed.
		try {
			haxe.Json.parse(trimmed);
		} catch (error:Dynamic) {
			return Invalid;
		}
		return findText(trimmed, 1);
	}

	static function findText(text:String, start:Int):TextKind {
		var index = start;
		var length = text.length;
		var found:TextKind = Missing;
		while (index < length) {
			index = skipSpace(text, index);
			if (index >= length) {
				break;
			}
			var current = text.charAt(index);
			if (current == "}") {
				return found;
			}
			if (current == ",") {
				index += 1;
				continue;
			}
			if (current != '"') {
				return Invalid;
			}
			var key = readString(text, index);
			if (key == null) {
				return Invalid;
			}
			index = key.next;
			index = skipSpace(text, index);
			if (index >= length || text.charAt(index) != ":") {
				return Invalid;
			}
			index = skipSpace(text, index + 1);
			if (index >= length) {
				return Invalid;
			}
			if (key.value == "text" && text.charAt(index) == '"') {
				var value = readString(text, index);
				if (value == null) {
					return Invalid;
				}
				found = Text(value.value);
				index = value.next;
				continue;
			}
			var after = skipValue(text, index);
			if (after < 0) {
				return Invalid;
			}
			index = after;
		}
		return found;
	}

	static function skipSpace(text:String, index:Int):Int {
		var length = text.length;
		while (index < length) {
			var current = text.charAt(index);
			if (current != " " && current != "\t" && current != "\n" && current != "\r") {
				break;
			}
			index += 1;
		}
		return index;
	}

	static function readString(text:String, index:Int):{value:String, next:Int} {
		if (text.charAt(index) != '"') {
			return null;
		}
		var out = new StringBuf();
		var cursor = index + 1;
		var length = text.length;
		while (cursor < length) {
			var current = text.charAt(cursor);
			cursor += 1;
			if (current == '"') {
				return {value: out.toString(), next: cursor};
			}
			if (current != "\\") {
				out.add(current);
				continue;
			}
			if (cursor >= length) {
				return null;
			}
			var escape = text.charAt(cursor);
			cursor += 1;
			switch (escape) {
				case '"': out.add('"');
				case "\\": out.add("\\");
				case "/": out.add("/");
				case "b": out.add("\x08");
				case "f": out.add("\x0c");
				case "n": out.add("\n");
				case "r": out.add("\r");
				case "t": out.add("\t");
				case "u":
					if (cursor + 4 > length) {
						return null;
					}
					var code = Std.parseInt("0x" + text.substr(cursor, 4));
					if (code == null) {
						return null;
					}
					cursor += 4;
					// A surrogate pair is two escapes; read the low half too.
					if (code >= 0xD800 && code <= 0xDBFF && cursor + 6 <= length && text.substr(cursor, 2) == "\\u") {
						var low = Std.parseInt("0x" + text.substr(cursor + 2, 4));
						if (low != null && low >= 0xDC00 && low <= 0xDFFF) {
							code = 0x10000 + ((code - 0xD800) << 10) + (low - 0xDC00);
							cursor += 6;
						}
					}
					out.add(String.fromCharCode(code));
				default:
					return null;
			}
		}
		return null;
	}

	/** Skips one JSON value and returns the index just past it, or -1. */
	static function skipValue(text:String, index:Int):Int {
		var length = text.length;
		if (index >= length) {
			return -1;
		}
		var current = text.charAt(index);
		if (current == '"') {
			var value = readString(text, index);
			return value == null ? -1 : value.next;
		}
		if (current == "{") {
			var depth = 0;
			var cursor = index;
			while (cursor < length) {
				var byte = text.charAt(cursor);
				if (byte == '"') {
					var value = readString(text, cursor);
					if (value == null) {
						return -1;
					}
					cursor = value.next;
					continue;
				}
				if (byte == "{") {
					depth += 1;
				} else if (byte == "}") {
					depth -= 1;
					if (depth == 0) {
						return cursor + 1;
					}
				}
				cursor += 1;
			}
			return -1;
		}
		if (current == "[") {
			var depth = 0;
			var cursor = index;
			while (cursor < length) {
				var byte = text.charAt(cursor);
				if (byte == '"') {
					var value = readString(text, cursor);
					if (value == null) {
						return -1;
					}
					cursor = value.next;
					continue;
				}
				if (byte == "[") {
					depth += 1;
				} else if (byte == "]") {
					depth -= 1;
					if (depth == 0) {
						return cursor + 1;
					}
				}
				cursor += 1;
			}
			return -1;
		}
		var cursor = index;
		while (cursor < length) {
			var byte = text.charAt(cursor);
			if (byte == "," || byte == "}" || byte == "]" || byte == " " || byte == "\t" || byte == "\n" || byte == "\r") {
				break;
			}
			cursor += 1;
		}
		return cursor == index ? -1 : cursor;
	}
}
