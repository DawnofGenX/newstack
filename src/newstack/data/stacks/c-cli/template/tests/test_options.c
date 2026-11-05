#include "check.h"

#include "textstat/options.h"

int run_options_tests(void) {
    int failures = 0;
    const char *files[8];

    {
        char *argv[] = {(char *)"counter", (char *)"-l", (char *)"a.txt", (char *)"b.txt"};
        const struct textstat_parse_result parsed = textstat_parse_args(4, argv, files);
        CHECK(parsed.status == TEXTSTAT_OK);
        CHECK(parsed.options.mode == TEXTSTAT_MODE_LINES);
        CHECK_SIZE(parsed.options.file_count, 2);
        CHECK_TEXT(parsed.options.files[0], "a.txt");
        CHECK_TEXT(parsed.options.files[1], "b.txt");
    }

    {
        char *argv[] = {(char *)"counter", (char *)"--words"};
        const struct textstat_parse_result parsed = textstat_parse_args(2, argv, files);
        CHECK(parsed.options.mode == TEXTSTAT_MODE_WORDS);
        /* No file means stdin, spelled as "-" so the caller has one code path. */
        CHECK_SIZE(parsed.options.file_count, 1);
        CHECK_TEXT(parsed.options.files[0], "-");
    }

    {
        char *argv[] = {(char *)"counter", (char *)"-c"};
        const struct textstat_parse_result parsed = textstat_parse_args(2, argv, files);
        CHECK(parsed.options.mode == TEXTSTAT_MODE_BYTES);
    }

    {
        char *argv[] = {(char *)"counter"};
        const struct textstat_parse_result parsed = textstat_parse_args(1, argv, files);
        CHECK(parsed.status == TEXTSTAT_OK);
        CHECK(parsed.options.mode == TEXTSTAT_MODE_ALL);
        CHECK_SIZE(parsed.options.file_count, 1);
        CHECK_TEXT(parsed.options.files[0], "-");
    }

    {
        char *argv[] = {(char *)"counter", (char *)"-l", (char *)"-c"};
        const struct textstat_parse_result parsed = textstat_parse_args(3, argv, files);
        /* Later flags win, exactly like wc. */
        CHECK(parsed.options.mode == TEXTSTAT_MODE_BYTES);
    }

    {
        char *argv[] = {(char *)"counter", (char *)"--help"};
        const struct textstat_parse_result parsed = textstat_parse_args(2, argv, files);
        CHECK(parsed.status == TEXTSTAT_HELP);
    }

    {
        char *argv[] = {(char *)"counter", (char *)"--version"};
        const struct textstat_parse_result parsed = textstat_parse_args(2, argv, files);
        CHECK(parsed.status == TEXTSTAT_PRINT_VERSION);
    }

    {
        char *argv[] = {(char *)"counter", (char *)"--bogus"};
        const struct textstat_parse_result parsed = textstat_parse_args(2, argv, files);
        CHECK(parsed.status == TEXTSTAT_USAGE_ERROR);
        CHECK_TEXT(parsed.error, "--bogus");
    }

    {
        /* Everything after -- is a file, even though it starts with a dash. */
        char *argv[] = {(char *)"counter", (char *)"--", (char *)"-l"};
        const struct textstat_parse_result parsed = textstat_parse_args(3, argv, files);
        CHECK(parsed.status == TEXTSTAT_OK);
        CHECK_SIZE(parsed.options.file_count, 1);
        CHECK_TEXT(parsed.options.files[0], "-l");
    }

    {
        /* A lone dash is stdin, not an option. */
        char *argv[] = {(char *)"counter", (char *)"-"};
        const struct textstat_parse_result parsed = textstat_parse_args(2, argv, files);
        CHECK(parsed.status == TEXTSTAT_OK);
        CHECK_SIZE(parsed.options.file_count, 1);
        CHECK_TEXT(parsed.options.files[0], "-");
    }

    return failures;
}
