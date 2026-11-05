#include "textstat/options.h"

#include <string.h>

static int is_mode_flag(const char *arg, enum textstat_mode *mode) {
    if (strcmp(arg, "-l") == 0 || strcmp(arg, "--lines") == 0) {
        *mode = TEXTSTAT_MODE_LINES;
        return 1;
    }
    if (strcmp(arg, "-w") == 0 || strcmp(arg, "--words") == 0) {
        *mode = TEXTSTAT_MODE_WORDS;
        return 1;
    }
    if (strcmp(arg, "-c") == 0 || strcmp(arg, "--bytes") == 0) {
        *mode = TEXTSTAT_MODE_BYTES;
        return 1;
    }
    return 0;
}

struct textstat_parse_result textstat_parse_args(int argc, char **argv, const char **files) {
    struct textstat_parse_result result;

    result.status = TEXTSTAT_OK;
    result.error = NULL;
    result.options.mode = TEXTSTAT_MODE_ALL;
    result.options.files = files;
    result.options.file_count = 0;

    int positional_only = 0;

    for (int i = 1; i < argc; i++) {
        const char *arg = argv[i];

        /* A lone "-" is the stdin marker, not an option. */
        const int looks_like_option = !positional_only && arg[0] == '-' && arg[1] != '\0';

        if (!looks_like_option) {
            files[result.options.file_count++] = arg;
            continue;
        }

        if (strcmp(arg, "--") == 0) {
            positional_only = 1;
            continue;
        }
        if (strcmp(arg, "-h") == 0 || strcmp(arg, "--help") == 0) {
            result.status = TEXTSTAT_HELP;
            return result;
        }
        if (strcmp(arg, "-V") == 0 || strcmp(arg, "--version") == 0) {
            result.status = TEXTSTAT_PRINT_VERSION;
            return result;
        }

        enum textstat_mode mode;
        if (is_mode_flag(arg, &mode)) {
            /* Later flags win: `-l -c` prints bytes, just like wc. */
            result.options.mode = mode;
            continue;
        }

        result.status = TEXTSTAT_USAGE_ERROR;
        result.error = arg;
        return result;
    }

    if (result.options.file_count == 0) {
        files[result.options.file_count++] = "-";
    }

    return result;
}

void textstat_usage(FILE *out, const char *program) {
    fprintf(out,
            "usage: %s [-l] [-w] [-c] [--] [file ...]\n"
            "\n"
            "Count lines, words and bytes. With no file, or when a file is -, read\n"
            "standard input. With several files a total is printed last.\n"
            "\n"
            "options:\n"
            "  -l, --lines    print the line count\n"
            "  -w, --words    print the word count\n"
            "  -c, --bytes    print the byte count\n"
            "  -h, --help     show this help and exit\n"
            "  -V, --version  print the version and exit\n",
            program);
}
