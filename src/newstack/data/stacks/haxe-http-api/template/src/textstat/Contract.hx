package textstat;

class Reply {
	public var status:Int;
	public var body:String;

	public function new(status:Int, body:String) {
		this.status = status;
		this.body = body;
	}
}

/**
 * The whole contract as one pure function: method, path, query and body in;
 * status and JSON body out. The socket layer only moves bytes.
 */
class Contract {
	public static function route(method:String, path:String, query:String, body:String):Reply {
		if (path == "/health" && method == "GET") {
			return new Reply(200, '{"status":"ok"}');
		}
		if (path == "/stats" && method == "GET") {
			var text = queryParam(query, "text");
			if (text == null) {
				return error(422, "missing_text", null);
			}
			return counts(text);
		}
		if (path == "/stats" && method == "POST") {
			return switch (JsonBody.read(body)) {
				case Invalid: error(422, "invalid_json", null);
				case Missing: error(422, "missing_text", null);
				case Text(value): counts(value);
			}
		}
		if (path == "/health" || path == "/stats") {
			return error(405, "method_not_allowed", null);
		}
		return error(404, "not_found", 'no route for $method $path');
	}

	static function counts(text:String):Reply {
		var totals = Counts.of(text);
		var body = '{"text":${quote(text)},"lines":${totals.lines},"words":${totals.words},"bytes":${totals.bytes}}';
		return new Reply(200, body);
	}

	static function error(status:Int, code:String, detail:String):Reply {
		var body = '{"error":${quote(code)}';
		if (detail != null) {
			body += ',"detail":${quote(detail)}';
		}
		body += "}";
		return new Reply(status, body);
	}

	public static function quote(value:String):String {
		var out = new StringBuf();
		out.add('"');
		for (index in 0...value.length) {
			var character = value.charAt(index);
			switch (character) {
				case '"': out.add('\\"');
				case "\\": out.add("\\\\");
				case "\n": out.add("\\n");
				case "\r": out.add("\\r");
				case "\t": out.add("\\t");
				default:
					var code = value.charCodeAt(index);
					if (code < 0x20) {
						out.add("\\u" + StringTools.hex(code, 4).toLowerCase());
					} else {
						out.add(character);
					}
			}
		}
		out.add('"');
		return out.toString();
	}

	static function queryParam(query:String, name:String):String {
		if (query == null || query.length == 0) {
			return null;
		}
		for (pair in query.split("&")) {
			if (pair.length == 0) {
				continue;
			}
			var split = pair.indexOf("=");
			var key = split < 0 ? pair : pair.substr(0, split);
			if (key != name) {
				continue;
			}
			return split < 0 ? "" : percentDecode(pair.substr(split + 1));
		}
		return null;
	}

	static function percentDecode(raw:String):String {
		var out = new StringBuf();
		var index = 0;
		while (index < raw.length) {
			var character = raw.charAt(index);
			if (character == "+") {
				out.add(" ");
				index += 1;
			} else if (character == "%" && index + 2 < raw.length) {
				var code = Std.parseInt("0x" + raw.substr(index + 1, 2));
				if (code == null) {
					out.add(character);
					index += 1;
				} else {
					// Decode to bytes, so multi-byte UTF-8 stays intact.
					var bytes = haxe.io.Bytes.alloc(1);
					bytes.set(0, code);
					out.add(bytes.toString());
					index += 3;
				}
			} else {
				out.add(character);
				index += 1;
			}
		}
		return out.toString();
	}
}
