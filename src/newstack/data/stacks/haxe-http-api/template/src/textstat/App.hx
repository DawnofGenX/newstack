package textstat;

/** Reads HOST and PORT and blocks in the accept loop. */
class App {
	static function main():Void {
		var host = Sys.getEnv("HOST");
		if (host == null || host == "") {
			host = "127.0.0.1";
		}
		var raw = Sys.getEnv("PORT");
		var port = raw == null || raw == "" ? 8080 : Std.parseInt(raw);
		Server.serve(host, port);
	}
}
