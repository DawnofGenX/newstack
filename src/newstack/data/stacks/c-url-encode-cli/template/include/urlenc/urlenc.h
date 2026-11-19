#ifndef URLENC_URLENC_H
#define URLENC_URLENC_H

#include <stddef.h>

/* Returns length needed for encoded output including NUL, or 0 on overflow. */
size_t url_encode(const char *src, char *dst, size_t dst_size);

/* Returns 0 on success, -1 on invalid percent sequence or overflow. */
int url_decode(const char *src, char *dst, size_t dst_size);

#endif
