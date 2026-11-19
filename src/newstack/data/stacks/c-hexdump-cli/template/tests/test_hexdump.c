#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "hexdump/hex.h"
#include "check.h"

int run_hex_tests(void) {
    int failures = 0;

    /* pinned: "Hello\n" */
    const unsigned char data[] = "Hello\n";
    char *out = hexdump_format(data, 6);
    CHECK_STR(out, "00000000  48 65 6c 6c 6f 0a                                 |Hello.          |\n");
    free(out);

    /* empty input yields empty output */
    char *empty = hexdump_format((const unsigned char *)"", 0);
    CHECK_STR(empty, "");
    free(empty);

    /* error: allocation contract returns non-null for valid input */
    CHECK(hexdump_format((const unsigned char *)"a", 1) != NULL);

    return failures;
}