#include "check.h"

#include "urlenc/urlenc.h"

#include <string.h>

int run_urlenc_tests(void) {
    int failures = 0;
    char buf[256];

    CHECK(url_encode("a b", buf, sizeof(buf)) == 5);
    CHECK_TEXT(buf, "a%20b");

    CHECK(url_encode("a~b", buf, sizeof(buf)) == 3);
    CHECK_TEXT(buf, "a~b");

    CHECK(url_decode("a%20b", buf, sizeof(buf)) == 0);
    CHECK_TEXT(buf, "a b");

    CHECK(url_decode("%7E", buf, sizeof(buf)) == 0);
    CHECK_TEXT(buf, "~");

    CHECK(url_decode("%ZZ", buf, sizeof(buf)) != 0);

    CHECK(url_encode("", buf, sizeof(buf)) == 0);
    CHECK_TEXT(buf, "");

    return failures;
}
