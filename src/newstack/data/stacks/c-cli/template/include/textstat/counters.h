#ifndef TEXTSTAT_COUNTERS_H
#define TEXTSTAT_COUNTERS_H

#include <stddef.h>

/* Line, word and byte totals for one input.
 *
 * Counting follows wc(1): a line is a '\n', a word is a maximal run of
 * non-whitespace bytes, and bytes is the raw payload length.
 */
struct textstat_counts {
    size_t lines;
    size_t words;
    size_t bytes;
};

/* Counts the bytes in data[0..length). data must not be NULL unless length is 0. */
struct textstat_counts textstat_count(const char *data, size_t length);

/* Adds two totals, so a caller can accumulate over several inputs. */
struct textstat_counts textstat_counts_add(struct textstat_counts total,
                                           struct textstat_counts item);

#endif /* TEXTSTAT_COUNTERS_H */
