#include "urlenc/urlenc.h"

#include <ctype.h>
#include <stdio.h>

static int is_unreserved(unsigned char c) {
    if ((c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') || (c >= '0' && c <= '9'))
        return 1;
    return c == '-' || c == '_' || c == '.' || c == '~';
}

static unsigned char hex_value(char c) {
    if (c >= '0' && c <= '9') return (unsigned char)(c - '0');
    if (c >= 'A' && c <= 'F') return (unsigned char)(c - 'A' + 10);
    if (c >= 'a' && c <= 'f') return (unsigned char)(c - 'a' + 10);
    return 0;
}

size_t url_encode(const char *src, char *dst, size_t dst_size) {
    size_t n = 0;
    if (dst_size == 0) return 0;
    for (; src && *src; src++) {
        if (is_unreserved((unsigned char)*src)) {
            if (n + 1 >= dst_size) return 0;
            dst[n++] = *src;
        } else {
            if (n + 3 >= dst_size) return 0;
            snprintf(dst + n, dst_size - n, "%%%02X", (unsigned char)*src);
            n += 3;
        }
    }
    if (n >= dst_size) return 0;
    dst[n] = '\0';
    return n;
}

int url_decode(const char *src, char *dst, size_t dst_size) {
    size_t n = 0;
    if (dst_size == 0) return -1;
    for (; src && *src; ) {
        if (*src == '%') {
            if (!isxdigit((unsigned char)src[1]) || !isxdigit((unsigned char)src[2]))
                return -1;
            unsigned char c = (unsigned char)((hex_value(src[1]) << 4) | hex_value(src[2]));
            if (n + 1 >= dst_size) return -1;
            dst[n++] = (char)c;
            src += 3;
        } else {
            if (n + 1 >= dst_size) return -1;
            dst[n++] = *src++;
        }
    }
    if (n >= dst_size) return -1;
    dst[n] = '\0';
    return 0;
}
