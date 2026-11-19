#include "hexdump/hex.h"

#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>

char *hexdump_format(const unsigned char *data, size_t length) {
    size_t lines = (length + 15) / 16;
    if (length == 0) {
        lines = 0;
    }
    size_t cap = lines * 80 + 16;
    if (cap < 16) {
        cap = 16;
    }
    char *out = malloc(cap);
    if (out == NULL) {
        return NULL;
    }
    size_t pos = 0;

    for (size_t off = 0; off < length; off += 16) {
        pos += (size_t)snprintf(out + pos, cap - pos, "%08zx  ", off);
        size_t chunk = length - off;
        if (chunk > 16) {
            chunk = 16;
        }
        for (size_t i = 0; i < 16; i++) {
            if (i < chunk) {
                pos += (size_t)snprintf(out + pos, cap - pos, "%02x ", data[off + i]);
            } else {
                pos += (size_t)snprintf(out + pos, cap - pos, "   ");
            }
            if (i == 7) {
                pos += (size_t)snprintf(out + pos, cap - pos, " ");
            }
        }
        pos += (size_t)snprintf(out + pos, cap - pos, " |");
        for (size_t i = 0; i < chunk; i++) {
            unsigned char c = data[off + i];
            out[pos++] = isprint(c) ? (char)c : '.';
        }
        for (size_t i = chunk; i < 16; i++) {
            out[pos++] = ' ';
        }
        out[pos++] = '|';
        out[pos++] = '\n';
    }

    out[pos] = '\0';
    return out;
}