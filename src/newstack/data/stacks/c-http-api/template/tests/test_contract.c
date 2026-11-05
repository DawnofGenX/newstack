#include "check.h"

#include "textstat/contract.h"

int run_contract_tests(void)
{
    int failures = 0;
    struct textstat_reply reply;

    reply = textstat_route("GET", "/health", "", "");
    CHECK_SIZE((size_t)reply.status, 200);
    CHECK_TEXT(reply.body, "{\"status\":\"ok\"}");
    textstat_reply_free(reply);

    reply = textstat_route("GET", "/stats", "text=hello%20world%0A", "");
    CHECK_SIZE((size_t)reply.status, 200);
    CHECK_TEXT(reply.body, "{\"text\":\"hello world\\n\",\"lines\":1,\"words\":2,\"bytes\":12}");
    textstat_reply_free(reply);

    /* A leading '?' is optional, and '+' is a space. */
    reply = textstat_route("GET", "/stats", "?text=a+b%0Ac%0A", "");
    CHECK_SIZE((size_t)reply.status, 200);
    CHECK_TEXT(reply.body, "{\"text\":\"a b\\nc\\n\",\"lines\":2,\"words\":3,\"bytes\":6}");
    textstat_reply_free(reply);

    reply = textstat_route("GET", "/stats", "other=1", "");
    CHECK_SIZE((size_t)reply.status, 422);
    CHECK_TEXT(reply.body, "{\"error\":\"missing_text\"}");
    textstat_reply_free(reply);

    reply = textstat_route("POST", "/stats", "", "{\"text\":\"a b\\nc\\n\"}");
    CHECK_SIZE((size_t)reply.status, 200);
    CHECK_TEXT(reply.body, "{\"text\":\"a b\\nc\\n\",\"lines\":2,\"words\":3,\"bytes\":6}");
    textstat_reply_free(reply);

    reply = textstat_route("POST", "/stats", "", "{\"text\":42}");
    CHECK_SIZE((size_t)reply.status, 422);
    CHECK_TEXT(reply.body, "{\"error\":\"missing_text\"}");
    textstat_reply_free(reply);

    reply = textstat_route("POST", "/stats", "", "{}");
    CHECK_SIZE((size_t)reply.status, 422);
    CHECK_TEXT(reply.body, "{\"error\":\"missing_text\"}");
    textstat_reply_free(reply);

    reply = textstat_route("POST", "/stats", "", "nope");
    CHECK_SIZE((size_t)reply.status, 422);
    CHECK_TEXT(reply.body, "{\"error\":\"invalid_json\"}");
    textstat_reply_free(reply);

    reply = textstat_route("GET", "/nope", "", "");
    CHECK_SIZE((size_t)reply.status, 404);
    CHECK_TEXT(reply.body, "{\"error\":\"not_found\",\"detail\":\"no route for GET /nope\"}");
    textstat_reply_free(reply);

    reply = textstat_route("DELETE", "/health", "", "");
    CHECK_SIZE((size_t)reply.status, 405);
    CHECK_TEXT(reply.body, "{\"error\":\"method_not_allowed\"}");
    textstat_reply_free(reply);

    /* Text that needs escaping on the way out. */
    reply = textstat_route("GET", "/stats", "text=%22quoted%22%09tab", "");
    CHECK_SIZE((size_t)reply.status, 200);
    CHECK_TEXT(reply.body,
               "{\"text\":\"\\\"quoted\\\"\\ttab\",\"lines\":0,\"words\":2,\"bytes\":12}");
    textstat_reply_free(reply);

    return failures;
}
