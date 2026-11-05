#include "check.h"

#include <stdlib.h>

#include "textstat/json.h"

int run_json_tests(void)
{
    int failures = 0;
    char *text = NULL;

    CHECK(textstat_json_read_text("{\"text\": \"a b\\nc\\n\"}", &text) == TEXTSTAT_JSON_TEXT);
    CHECK_TEXT(text, "a b\nc\n");
    free(text);
    text = NULL;

    /* A number where the string belongs is "missing", not "invalid". */
    CHECK(textstat_json_read_text("{\"text\": 42}", &text) == TEXTSTAT_JSON_MISSING);
    CHECK(text == NULL);

    CHECK(textstat_json_read_text("{\"other\": \"x\"}", &text) == TEXTSTAT_JSON_MISSING);
    CHECK(textstat_json_read_text("{}", &text) == TEXTSTAT_JSON_MISSING);
    CHECK(textstat_json_read_text("  {  }  ", &text) == TEXTSTAT_JSON_MISSING);

    /* Everything else is not a JSON object at all. */
    CHECK(textstat_json_read_text("nope", &text) == TEXTSTAT_JSON_INVALID);
    CHECK(textstat_json_read_text("", &text) == TEXTSTAT_JSON_INVALID);
    CHECK(textstat_json_read_text("[\"text\"]", &text) == TEXTSTAT_JSON_INVALID);
    CHECK(textstat_json_read_text("{\"text\": \"unterminated}", &text) == TEXTSTAT_JSON_INVALID);
    CHECK(textstat_json_read_text("{\"text\": \"a\"} trailing", &text) == TEXTSTAT_JSON_INVALID);
    CHECK(textstat_json_read_text(NULL, &text) == TEXTSTAT_JSON_INVALID);

    /* Escapes, including a surrogate pair, come back as UTF-8. */
    CHECK(textstat_json_read_text("{\"text\": \"a\\u00e9\"}", &text) == TEXTSTAT_JSON_TEXT);
    CHECK_TEXT(text, "aé");
    free(text);
    text = NULL;

    CHECK(textstat_json_read_text("{\"text\": \"\\ud83d\\ude42\"}", &text) == TEXTSTAT_JSON_TEXT);
    CHECK_TEXT(text, "🙂");
    free(text);
    text = NULL;

    CHECK(textstat_json_read_text("{\"text\": \"quote \\\" slash \\\\ tab \\t\"}", &text) ==
          TEXTSTAT_JSON_TEXT);
    CHECK_TEXT(text, "quote \" slash \\ tab \t");
    free(text);
    text = NULL;

    /* Nested values are allowed in other members and are skipped cleanly. */
    CHECK(textstat_json_read_text("{\"meta\": {\"a\": [1, 2, {\"b\": null}]}, \"text\": \"hi\"}",
                                  &text) == TEXTSTAT_JSON_TEXT);
    CHECK_TEXT(text, "hi");
    free(text);

    return failures;
}
