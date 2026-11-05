import textstat.Contract;
import textstat.Counts;
import textstat.JsonBody;
import textstat.TextKind;

/**
 * Runs with `haxe -cp src -cp tests --interp -main TextstatTests`: no test
 * framework, no build output, just checks that exit non-zero on failure.
 */
class TextstatTests {
	static var passed = 0;
	static var failed = 0;

	static function main():Void {
		countsTests();
		jsonTests();
		contractTests();
		Sys.println('checks: ${passed + failed}, passed: $passed, failed: $failed');
		Sys.exit(failed == 0 ? 0 : 1);
	}

	static function check(name:String, ok:Bool):Void {
		if (ok) {
			passed += 1;
			return;
		}
		failed += 1;
		Sys.println('FAIL $name');
	}

	static function same(name:String, got:Dynamic, want:Dynamic):Void {
		if (Std.string(got) == Std.string(want)) {
			passed += 1;
			return;
		}
		failed += 1;
		Sys.println('FAIL $name (got ${Std.string(got)}, want ${Std.string(want)})');
	}

	static function countsAre(name:String, text:String, lines:Int, words:Int, bytes:Int):Void {
		var totals = Counts.of(text);
		same('$name: lines', totals.lines, lines);
		same('$name: words', totals.words, words);
		same('$name: bytes', totals.bytes, bytes);
	}

	static function countsTests():Void {
		countsAre("empty input", "", 0, 0, 0);
		countsAre("one line", "hello world\n", 1, 2, 12);
		countsAre("two lines", "a b\nc\n", 2, 3, 6);
		countsAre("blank lines", "\n\nx\n", 3, 1, 4);
		countsAre("spaces only", "  \t ", 0, 0, 4);
		countsAre("no trailing newline", "abc", 0, 1, 3);
		countsAre("utf-8 payload", "héllo wörld\n", 1, 2, 14);
		countsAre("emoji", "🙂\n", 1, 1, 5);
	}

	static function kindOf(body:String):String {
		return switch (JsonBody.read(body)) {
			case Invalid: "invalid";
			case Missing: "missing";
			case Text(value): 'text:$value';
		};
	}

	static function jsonTests():Void {
		same("a string member is read", kindOf('{"text":"a b\\nc\\n"}'), "text:a b\nc\n");
		same("unicode escapes are decoded", kindOf('{"text":"h\\u00e9llo"}'), "text:héllo");
		same("surrogate pairs are decoded", kindOf('{"text":"\\ud83d\\ude42"}'), "text:🙂");
		same("a number is missing", kindOf('{"text":42}'), "missing");
		same("null is missing", kindOf('{"text":null}'), "missing");
		same("an object is missing", kindOf('{"text":{"a":1}}'), "missing");
		same("an absent member is missing", kindOf('{"body":"x"}'), "missing");
		same("an empty object is missing", kindOf("{}"), "missing");
		same("a bare word is invalid", kindOf("nope"), "invalid");
		same("an array is invalid", kindOf('["text"]'), "invalid");
		same("trailing data is invalid", kindOf('{"text":"a"} trailing'), "invalid");
		same("an unterminated string is invalid", kindOf('{"text":"a}'), "invalid");
		same("other members are skipped", kindOf('{"n":1,"text":"x","f":true,"o":{"k":[1,2]}}'), "text:x");
	}

	static function statusIs(name:String, method:String, path:String, query:String, body:String, status:Int):Void {
		same('$name: status', Contract.route(method, path, query, body).status, status);
	}

	static function contractTests():Void {
		statusIs("health", "GET", "/health", "", "", 200);
		same("health body", Contract.route("GET", "/health", "", "").body, '{"status":"ok"}');

		var get = Contract.route("GET", "/stats", "text=hello%20world%0A", "");
		same("a query is counted: status", get.status, 200);
		same("a query is counted: body", get.body, '{"text":"hello world\\n","lines":1,"words":2,"bytes":12}');

		var plus = Contract.route("GET", "/stats", "text=hello+world", "");
		same("plus is a space", plus.body, '{"text":"hello world","lines":0,"words":2,"bytes":11}');

		var post = Contract.route("POST", "/stats", "", '{"text":"a b\\nc\\n"}');
		same("a body is counted: status", post.status, 200);
		same("a body is counted: body", post.body, '{"text":"a b\\nc\\n","lines":2,"words":3,"bytes":6}');

		var utf8 = Contract.route("POST", "/stats", "", '{"text":"h\\u00e9llo w\\u00f6rld\\n"}');
		same("utf-8 bytes, not characters", utf8.body, '{"text":"héllo wörld\\n","lines":1,"words":2,"bytes":14}');

		statusIs("no text", "GET", "/stats", "", "", 422);
		same("no text is missing_text", Contract.route("GET", "/stats", "", "").body, '{"error":"missing_text"}');
		same("an empty value is zero", Contract.route("GET", "/stats", "text=", "").body, '{"text":"","lines":0,"words":0,"bytes":0}');

		statusIs("a number is rejected", "POST", "/stats", "", '{"text":42}', 422);
		same("a number is missing_text", Contract.route("POST", "/stats", "", '{"text":42}').body, '{"error":"missing_text"}');
		statusIs("broken JSON is rejected", "POST", "/stats", "", "nope", 422);
		same("broken JSON is invalid_json", Contract.route("POST", "/stats", "", "nope").body, '{"error":"invalid_json"}');

		statusIs("a known path, wrong method", "DELETE", "/health", "", "", 405);
		same("405 body", Contract.route("DELETE", "/health", "", "").body, '{"error":"method_not_allowed"}');

		statusIs("an unknown path", "GET", "/nope", "", "", 404);
		same("404 names the route", Contract.route("GET", "/nope", "", "").body, '{"error":"not_found","detail":"no route for GET /nope"}');

		var quoted = Contract.route("POST", "/stats", "", '{"text":"a\\"quote\\""}');
		same("quotes survive both ways", quoted.body, '{"text":"a\\"quote\\"","lines":0,"words":1,"bytes":8}');
	}
}
