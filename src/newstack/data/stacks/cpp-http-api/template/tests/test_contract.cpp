#include "check.hpp"

namespace {

using textstat::Reply;
using textstat::check::equal;
using textstat::check::report;
using textstat::route;

void status_is(std::string_view name, const Reply &reply, long long status) {
    equal(name, static_cast<long long>(reply.status), status);
}

}  // namespace

void contract_tests() {
    status_is("health is 200", route("GET", "/health", "", ""), 200);
    equal("health body", route("GET", "/health", "", "").body, R"({"status":"ok"})");

    const Reply get = route("GET", "/stats", "text=hello%20world%0A", "");
    status_is("a query is counted", get, 200);
    equal("query body", get.body,
          R"({"text":"hello world\n","lines":1,"words":2,"bytes":12})");

    const Reply percent = route("GET", "/stats", "text=hello+world", "");
    equal("plus is a space", percent.body,
          R"({"text":"hello world","lines":0,"words":2,"bytes":11})");

    const Reply post = route("POST", "/stats", "", R"({"text":"a b\nc\n"})");
    status_is("a body is counted", post, 200);
    equal("body answer", post.body, R"({"text":"a b\nc\n","lines":2,"words":3,"bytes":6})");

    const Reply utf8 = route("POST", "/stats", "", R"({"text":"h\u00e9llo w\u00f6rld\n"})");
    // A raw string would keep \xc3 literal, so the expected value is built from
    // ordinary escapes: the reader must hand back real UTF-8 bytes.
    equal("utf-8 bytes, not characters", utf8.body,
          "{\"text\":\"h" "\xc3\xa9" "llo w" "\xc3\xb6" "rld\\n\",\"lines\":1,\"words\":2,\"bytes\":14}");

    status_is("no text is 422", route("GET", "/stats", "", ""), 422);
    equal("no text is missing_text", route("GET", "/stats", "", "").body,
          R"({"error":"missing_text"})");
    status_is("an empty value still counts", route("GET", "/stats", "text=", ""), 200);
    equal("an empty value is zero", route("GET", "/stats", "text=", "").body,
          R"({"text":"","lines":0,"words":0,"bytes":0})");

    const Reply number = route("POST", "/stats", "", R"({"text":42})");
    status_is("a number is 422", number, 422);
    equal("a number is missing_text", number.body, R"({"error":"missing_text"})");

    const Reply broken = route("POST", "/stats", "", "nope");
    status_is("broken JSON is 422", broken, 422);
    equal("broken JSON is invalid_json", broken.body, R"({"error":"invalid_json"})");

    status_is("a known path, wrong method is 405", route("DELETE", "/health", "", ""), 405);
    status_is("bad words are 405 too", route("PUT", "/stats", "text=a", ""), 405);
    equal("405 body", route("DELETE", "/health", "", "").body,
          R"({"error":"method_not_allowed"})");

    const Reply gone = route("GET", "/nope", "", "");
    status_is("an unknown path is 404", gone, 404);
    equal("404 names the route", gone.body,
          R"({"error":"not_found","detail":"no route for GET /nope"})");

    const Reply quoted = route("POST", "/stats", "", R"({"text":"a\"quote\""})");
    const char mark = '\\';
    const std::string quoted_want = std::string("{\"text\":\"a") + mark + "\"quote" + mark +
                                    "\"\",\"lines\":0,\"words\":1,\"bytes\":8}";
    equal("quotes are escaped on the way out", quoted.body, quoted_want);
}
