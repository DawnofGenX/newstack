import "dart:convert";

import "package:shelf/shelf.dart";
import "package:shelf_router/shelf_router.dart";

import "counts.dart";

/// Builds the service as a plain [Handler].
///
/// Returning a handler rather than a listening server is what keeps the tests fast and
/// deterministic: they call the same function object the socket drives, with no port and
/// no retry loop.
Handler buildHandler() {
  final router =
      Router(notFoundHandler: _notFound)
        ..get("/health", _health)
        ..get("/stats", _stats)
        ..post("/stats", _statsFromBody);
  return const Pipeline().addMiddleware(logRequests()).addHandler(router.call);
}

Response _health(Request request) => _json(200, <String, Object?>{"status": "ok"});

Response _stats(Request request) {
  final text = request.url.queryParameters["text"];
  if (text == null) {
    return _json(422, <String, Object?>{"error": "missing_text"});
  }
  return _json(200, countsJson(text, countText(text)));
}

Future<Response> _statsFromBody(Request request) async {
  final body = await request.readAsString();
  Object? decoded;
  try {
    decoded = jsonDecode(body);
  } on FormatException {
    return _json(422, <String, Object?>{"error": "invalid_json"});
  }
  if (decoded is! Map<String, Object?> || decoded["text"] is! String) {
    return _json(422, <String, Object?>{"error": "missing_text"});
  }
  final text = decoded["text"]! as String;
  return _json(200, countsJson(text, countText(text)));
}

Response _notFound(Request request) => _json(404, <String, Object?>{
  "error": "not_found",
  "detail": "no route for ${request.method} /${request.url.path}",
});

Response _json(int status, Map<String, Object?> body) => Response(
  status,
  body: jsonEncode(body),
  headers: <String, String>{"content-type": "application/json"},
);
