#include "textstat/counters.h"

#include <ctype.h>

struct textstat_counts textstat_count(const char *data, size_t length) {
    struct textstat_counts counts = {0, 0, 0};
    int in_word = 0;

    for (size_t i = 0; i < length; i++) {
        const unsigned char byte = (unsigned char)data[i];

        if (byte == '\n') {
            counts.lines++;
        }

        /* isspace() takes an unsigned char value; casting above also stops a
         * negative char from being read as EOF on platforms where char is signed. */
        if (isspace(byte)) {
            in_word = 0;
        } else if (!in_word) {
            in_word = 1;
            counts.words++;
        }
    }

    counts.bytes = length;
    return counts;
}

struct textstat_counts textstat_counts_add(struct textstat_counts total,
                                           struct textstat_counts item) {
    total.lines += item.lines;
    total.words += item.words;
    total.bytes += item.bytes;
    return total;
}
