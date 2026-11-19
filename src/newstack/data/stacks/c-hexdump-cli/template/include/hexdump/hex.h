#ifndef HEXDUMP_HEX_H
#define HEXDUMP_HEX_H

#include <stddef.h>

/* Format `length` bytes of `data` into a classic hex dump:
 *   00000000  48 65 6c 6c 6f 0a           |Hello.|
 * Returns a malloc'd NUL-terminated string (caller frees), or NULL on
 * allocation failure. When `data` is NULL and length is 0, returns an
 * empty string. */
char *hexdump_format(const unsigned char *data, size_t length);

#endif /* HEXDUMP_HEX_H */