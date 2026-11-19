#include "hexdump/hex.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static const char *program_name(const char *argv0) {
    if (argv0 == NULL || *argv0 == '\0') {
        return "hexdump";
    }
    const char *slash = strrchr(argv0, '/');
    return slash != NULL ? slash + 1 : argv0;
}

static char *read_all(FILE *stream, size_t *length) {
    size_t capacity = 8192;
    size_t used = 0;
    char *buffer = malloc(capacity);
    if (buffer == NULL) {
        return NULL;
    }
    for (;;) {
        if (used == capacity) {
            size_t grown = capacity * 2;
            char *bigger = realloc(buffer, grown);
            if (bigger == NULL) {
                free(buffer);
                return NULL;
            }
            buffer = bigger;
            capacity = grown;
        }
        size_t got = fread(buffer + used, 1, capacity - used, stream);
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

static int dump_file(const char *path) {
    FILE *f;
    int from_stdin = (strcmp(path, "-") == 0);
    if (from_stdin) {
        f = stdin;
    } else {
        f = fopen(path, "rb");
        if (f == NULL) {
            fprintf(stderr, "hexdump: cannot open '%s'\n", path);
            return 1;
        }
    }
    size_t length = 0;
    char *data = read_all(f, &length);
    if (!from_stdin) {
        fclose(f);
    }
    if (data == NULL && length == 0 && ferror(f)) {
        /* read_all already handled; fall through */
    }
    if (data == NULL && length != 0) {
        fprintf(stderr, "hexdump: out of memory\n");
        return 1;
    }
    char *out = hexdump_format((const unsigned char *)data, length);
    if (out == NULL) {
        free(data);
        fprintf(stderr, "hexdump: out of memory\n");
        return 1;
    }
    fputs(out, stdout);
    free(out);
    free(data);
    return 0;
}

static void usage(const char *prog) {
    printf("Usage: %s [FILE...]\n", prog);
    printf("Print a hexadecimal dump of each FILE (or stdin).\n");
    printf("Options:\n");
    printf("  -h, --help     show this help and exit\n");
    printf("  -v, --version  show version and exit\n");
}

int main(int argc, char **argv) {
    const char *prog = program_name(argv[0]);
    if (argc == 1) {
        return dump_file("-");
    }
    /* parse options */
    int i = 1;
    /* handle flags */
    /* simple: if first arg is flag */
    for (i = 1; i < argc; i++) {
        if (strcmp(argv[i], "-h") == 0 || strcmp(argv[i], "--help") == 0) {
            usage(prog);
            return 0;
        }
        if (strcmp(argv[i], "-v") == 0 || strcmp(argv[i], "--version") == 0) {
            printf("hexdump 1.0.0\n");
            return 0;
        }
        if (argv[i][0] == '-' && argv[i][1] != '\0' && strcmp(argv[i], "-") != 0) {
            fprintf(stderr, "hexdump: unknown option '%s'\n", argv[i]);
            return 2;
        }
    }
    int rc = 0;
    int any = 0;
    for (i = 1; i < argc; i++) {
        if (argv[i][0] == '-' && strcmp(argv[i], "-") != 0) {
            continue; /* already handled */
        }
        any = 1;
        int r = dump_file(argv[i]);
        if (r != 0) {
            rc = r;
        }
    }
    if (!any) {
        return dump_file("-");
    }
    return rc;
}