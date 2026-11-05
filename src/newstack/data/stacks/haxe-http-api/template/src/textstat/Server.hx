package textstat;

import sys.net.Host;
import sys.net.Socket;
import haxe.io.Error;

/** One request per connection on a blocking socket, until the process exits. */
class Server {
	public static function serve(host:String, port:Int):Void {
		var listener = new Socket();
		listener.setBlocking(true);
		listener.bind(new Host(host), port);
		listener.listen(16);
		trace('listening on http://$host:$port');
		while (true) {
			var client = listener.accept();
			try {
				handle(client);
			} catch (error:Dynamic) {
				// A client that walks away mid-request must not stop the loop.
			}
			linger(client);
		}
	}

	/**
	 * Waits for the client to hang up before closing our side, so the
	 * TIME_WAIT of this connection sits on the client's ephemeral port.
	 *
	 * Closing first parks the *listening* port in TIME_WAIT for a minute, and
	 * Haxe cannot ask for SO_REUSEADDR: the next run then dies in
	 * `listener.bind` with `Unix.Unix_error(Unix.EADDRINUSE, "bind", "")`
	 * while `ss -ltn` insists the port is free. The drain is non-blocking with
	 * a one-second cap, so a client that never closes cannot wedge the loop.
	 */
	static function linger(client:Socket):Void {
		try {
			client.setBlocking(false);
		} catch (error:Dynamic) {}
		var deadline = Sys.time() + 1.0;
		while (Sys.time() < deadline) {
			try {
				client.input.readByte();
			} catch (eof:haxe.io.Eof) {
				break;
			} catch (blocked:haxe.io.Error) {
				if (blocked != Blocked) {
					break;
				}
				Sys.sleep(0.005);
			} catch (other:Dynamic) {
				break;
			}
		}
		client.close();
	}

	static function handle(client:Socket):Void {
		var requestLine = readLine(client);
		if (requestLine == null) {
			return;
		}
		var parts = requestLine.split(" ");
		if (parts.length < 3) {
			respond(client, 422, '{"error":"bad_request"}');
			return;
		}
		var target = parts[1];
		var length = 0;
		while (true) {
			var line = readLine(client);
			if (line == null || line == "") {
				break;
			}
			var colon = line.indexOf(":");
			if (colon > 0 && line.substr(0, colon).toLowerCase() == "content-length") {
				length = Std.parseInt(StringTools.trim(line.substr(colon + 1)));
				if (length == null) {
					length = 0;
				}
			}
		}
		if (length > 65536) {
			respond(client, 413, '{"error":"body_too_large"}');
			return;
		}
		var body = length > 0 ? client.input.read(length).toString() : "";
		var mark = target.indexOf("?");
		var path = mark < 0 ? target : target.substr(0, mark);
		var query = mark < 0 ? "" : target.substr(mark + 1);
		var reply = Contract.route(parts[0], path, query, body);
		respond(client, reply.status, reply.body);
	}

	static function readLine(client:Socket):String {
		var line = client.input.readLine();
		if (line == null) {
			return null;
		}
		return StringTools.trim(line);
	}

	static function reason(status:Int):String {
		return switch (status) {
			case 200: "OK";
			case 404: "Not Found";
			case 405: "Method Not Allowed";
			case 413: "Content Too Large";
			case 422: "Unprocessable Entity";
			case _: "Internal Server Error";
		}
	}

	static function respond(client:Socket, status:Int, body:String):Void {
		var output = client.output;
		output.writeString('HTTP/1.1 $status ${reason(status)}\r\n');
		output.writeString("content-type: application/json\r\n");
		output.writeString("content-length: " + haxe.io.Bytes.ofString(body).length + "\r\n");
		output.writeString("connection: close\r\n\r\n");
		output.writeString(body);
		output.flush();
	}
}
