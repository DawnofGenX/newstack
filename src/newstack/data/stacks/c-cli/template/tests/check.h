#ifndef TEXTSTAT_CHECK_H
#define TEXTSTAT_CHECK_H

/* A twenty-line assertion header instead of a test framework.
 *
 * Each suite is a function returning its failure count, so the runner in
 * tests/main.c can add them up and exit non-zero on any failure. Link a real
 * framework (Unity, greatest, cmocka) when the project outgrows this file.
 */

#include <stdio.h>
#include <string.h>

#define CHECK(condition)                                                                      \
    do {                                                                                      \
        if (!(condition)) {                                                                   \
            fprintf(stderr, "%s:%d: check failed: %s\n", __FILE__, __LINE__, #condition);      \
            failures++;                                                                        \
        }                                                                                      \
    } while (0)

#define CHECK_SIZE(actual, expected)                                                           \
    do {                                                                                       \
        const size_t check_got = (size_t)(actual);                                             \
        const size_t check_want = (size_t)(expected);                                          \
        if (check_got != check_want) {                                                         \
            fprintf(stderr, "%s:%d: expected %zu, got %zu\n", __FILE__, __LINE__, check_want,   \
                    check_got);                                                                \
            failures++;                                                                        \
        }                                                                                      \
    } while (0)

#define CHECK_TEXT(actual, expected)                                                           \
    do {                                                                                       \
        const char *check_got = (actual);                                                      \
        const char *check_want = (expected);                                                   \
        if (check_got == NULL || strcmp(check_got, check_want) != 0) {                          \
            fprintf(stderr, "%s:%d: expected \"%s\", got \"%s\"\n", __FILE__, __LINE__,         \
                    check_want, check_got == NULL ? "(null)" : check_got);                      \
            failures++;                                                                        \
        }                                                                                      \
    } while (0)

#endif /* TEXTSTAT_CHECK_H */
