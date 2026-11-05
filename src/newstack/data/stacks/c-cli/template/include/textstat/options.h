#ifndef TEXTSTAT_OPTIONS_H
#define TEXTSTAT_OPTIONS_H

#include <stddef.h>
#include <stdio.h>

#define TEXTSTAT_VERSION "0.1.0"

enum textstat_mode {
    TEXTSTAT_MODE_ALL,
    TEXTSTAT_MODE_LINES,
    TEXTSTAT_MODE_WORDS,
    TEXTSTAT_MODE_BYTES
};

enum textstat_status {
    TEXTSTAT_OK,
    TEXTSTAT_HELP,
    TEXTSTAT_PRINT_VERSION,
    TEXTSTAT_USAGE_ERROR
};

struct textstat_options {
    enum textstat_mode mode;
    const char **files;
    size_t file_count;
};

struct textstat_parse_result {
    enum textstat_status status;
    struct textstat_options options;
    /* Points at the offending argv entry for TEXTSTAT_USAGE_ERROR, else NULL. */
    const char *error;
};

/* Parses argv, where argv[0] is the program name.
 *
 * files must have room for argc pointers; ownership stays with the caller, and the
 * entries point straight into argv, so nothing here allocates. */
struct textstat_parse_result textstat_parse_args(int argc, char **argv, const char **files);

void textstat_usage(FILE *out, const char *program);

#endif /* TEXTSTAT_OPTIONS_H */
