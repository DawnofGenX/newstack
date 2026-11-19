#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "urlenc/urlenc.h"

static void usage(const char *program) {
    printf("Usage: %s encode STRING\n", program);
    printf("       %s decode STRING\n", program);
    printf("Percent-encode or decode a string per RFC 3986.\n");
}

int main(int argc, char **argv) {
    const char *program = "{{ npm_name }}";
    if (argc < 2 || strcmp(argv[1], "--help") == 0 || strcmp(argv[1], "-h") == 0) {
        usage(program);
        return (argc < 2) ? 2 : 0;
    }
    if (strcmp(argv[1], "--version") == 0) {
        printf("0.1.0\n");
        return 0;
    }
    if (argc < 3) {
        fprintf(stderr, "missing string\n");
        usage(program);
        return 2;
    }
    if (strcmp(argv[1], "encode") != 0 && strcmp(argv[1], "decode") != 0) {
        fprintf(stderr, "unknown command: %s\n", argv[1]);
        usage(program);
        return 2;
    }

    char buffer[4096];
    if (strcmp(argv[1], "encode") == 0) {
        if (url_encode(argv[2], buffer, sizeof(buffer)) == 0 && argv[2][0] != '\0') {
            /* empty input encodes to empty, so check separately */
        }
        printf("%s\n", buffer);
        return 0;
    }

    if (url_decode(argv[2], buffer, sizeof(buffer)) != 0) {
        fprintf(stderr, "invalid percent sequence: %s\n", argv[2]);
        return 2;
    }
    printf("%s\n", buffer);
    return 0;
}
