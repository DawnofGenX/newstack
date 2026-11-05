import "dart:convert";

import "package:shelf/shelf.dart";
import "package:test/test.dart";
import "package:{{ package_name }}/{{ package_name }}.dart";

/// Drives the handler the socket serves, with no port and no timing.
Future<Map<String, Object?>> call(
  Handler handler,
  String method,
  String path, {
  String? body,
}) async {
  final response = await handler(
    Request(
      method,
      Uri.parse("http://localhost$path"),
      body: body,
      headers: body == null ? null : <String, String>{"content-type": "application/json"},
    ),
  );
  final decoded = jsonDecode(await response.readAsString()) as Map<String, Object?>;
  return <String, Object?>{...decoded, "_status": response.statusCode};
}

void main() {
  final handler = buildHandler();

  test("GET /health", () async {
    expect(await call(handler, "GET", "/health"), <String, Object?>{'status': 'ok', '_status': 200});
  });

  test("GET /stats counts the query parameter", () async {
    expect(
      await call(handler, "GET", "/stats?text=hello%20world%0A"),
      <String, Object?>{
        "text": "hello world\n",
        "lines": 1,
        "words": 2,
        "bytes": 12,
        "_status": 200,
      },
    );
  });

  test("GET /stats treats an empty parameter as empty text, not as missing", () async {
    expect(await call(handler, "GET", "/stats?text="), <String, Object?>{
      "text": "",
      "lines": 0,
      "words": 0,
      "bytes": 0,
      "_status": 200,
    });
  });

  test("GET /stats without a parameter is a 422", () async {
    expect(await call(handler, "GET", "/stats"), <String, Object?>{
      "error": "missing_text",
      "_status": 422,
    });
  });

  test("POST /stats counts the body", () async {
    expect(await call(handler, "POST", "/stats", body: '{"text":"a b\\nc\\n"}'), <String, Object?>{
      "text": "a b\nc\n",
      "lines": 2,
      "words": 3,
      "bytes": 6,
      "_status": 200,
    });
  });

  test("POST /stats preserves padding exactly as sent", () async {
    expect(await call(handler, "POST", "/stats", body: '{"text":"  padded  \\n"}'), <String, Object?>{
      "text": "  padded  \n",
      "lines": 1,
      "words": 1,
      "bytes": 11,
      "_status": 200,
    });
  });

  test("POST /stats rejects a non-JSON body with 422", () async {
    expect(await call(handler, "POST", "/stats", body: "not json"), <String, Object?>{
      "error": "invalid_json",
      "_status": 422,
    });
  });

  test("POST /stats rejects a non-string text with 422", () async {
    expect(await call(handler, "POST", "/stats", body: '{"text":42}'), <String, Object?>{
      "error": "missing_text",
      "_status": 422,
    });
  });

  test("an unknown route is a JSON 404", () async {
    expect(await call(handler, "GET", "/nope"), <String, Object?>{
      "error": "not_found",
      "detail": "no route for GET /nope",
      "_status": 404,
    });
  });
}
