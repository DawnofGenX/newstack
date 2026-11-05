#include "textstat/counters.h"
#include "textstat/options.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static const char *program_name(const char *argv0) {
    if (argv0 == NULL || *argv0 == '\0') {
        return "counter";
    }
    const char *slash = strrchr(argv0, '/');
    return slash != NULL ? slash + 1 : argv0;
}

/* Reads the whole stream into one malloc'd buffer, so counting does not care
 * whether the input is a file, a pipe or a terminal. */
static char *read_all(FILE *stream, size_t *length) {
    size_t capacity = 8192;
    size_t used = 0;
    char *buffer = malloc(capacity);

    if (buffer == NULL) {
        return NULL;
    }

    for (;;) {
        if (used == capacity) {
            const size_t grown = capacity * 2;
            char *bigger = realloc(buffer, grown);
            if (bigger == NULL) {
                free(buffer);
                return NULL;
            }
            buffer = bigger;
            capacity = grown;
        }

        const size_t got = fread(buffer + used, 1, capacity - used, stream);
        used += got;

        if (got == 0) {
            if (ferror(stream)) {
                free(buffer);
                return NULL;
            }
            break;
        }
    }

    *length = used;
    return buffer;
}

static void print_counts(struct textstat_counts counts, enum textstat_mode mode,
                         const char *label) {
    const int all = mode == TEXTSTAT_MODE_ALL;

    if (all || mode == TEXTSTAT_MODE_LINES) {
        printf("%8zu", counts.lines);
    }
    if (all || mode == TEXTSTAT_MODE_WORDS) {
        printf("%8zu", counts.words);
    }
    if (all || mode == TEXTSTAT_MODE_BYTES) {
        printf("%8zu", counts.bytes);
    }
    if (label != NULL) {
        printf(" %s", label);
    }
    putchar('\n');
}

static int count_inputs(const struct textstat_options *options) {
    struct textstat_counts total = {0, 0, 0};
    int failed = 0;

    for (size_t i = 0; i < options->file_count; i++) {
        const char *path = options->files[i];
        const int from_stdin = strcmp(path, "-") == 0;

        FILE *stream = from_stdin ? stdin : fopen(path, "rb");
        if (stream == NULL) {
            fprintf(stderr, "error: cannot open '%s'\n", path);
            failed = 1;
            continue;
        }

        size_t length = 0;
        char *buffer = read_all(stream, &length);
        if (!from_stdin) {
            fclose(stream);
        }
        if (buffer == NULL) {
            fprintf(stderr, "error: cannot read '%s'\n", path);
            failed = 1;
            continue;
        }

        const struct textstat_counts counts = textstat_count(buffer, length);
        free(buffer);

        total = textstat_counts_add(total, counts);
        print_counts(counts, options->mode, from_stdin ? NULL : path);
    }

    if (options->file_count > 1) {
        print_counts(total, options->mode, "total");
    }

    return failed ? 1 : 0;
}

int main(int argc, char **argv) {
    const char *program = program_name(argc > 0 ? argv[0] : NULL);
    const int capacity = argc > 0 ? argc : 1;

    const char **files = calloc((size_t)capacity, sizeof *files);
    if (files == NULL) {
        fprintf(stderr, "error: out of memory\n");
        return 1;
    }

    const struct textstat_parse_result parsed = textstat_parse_args(argc, argv, files);
    int exit_code;

    switch (parsed.status) {
    case TEXTSTAT_HELP:
        textstat_usage(stdout, program);
        exit_code = 0;
        break;
    case TEXTSTAT_PRINT_VERSION:
        printf("%s %s\n", program, TEXTSTAT_VERSION);
        exit_code = 0;
        break;
    case TEXTSTAT_USAGE_ERROR:
        fprintf(stderr, "error: unrecognised option '%s'\n\n", parsed.error);
        textstat_usage(stderr, program);
        exit_code = 2;
        break;
    case TEXTSTAT_OK:
    default:
        exit_code = count_inputs(&parsed.options);
        break;
    }

    free(files);
    return exit_code;
}
