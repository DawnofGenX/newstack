#ifndef HEXDUMP_CHECK_H
#define HEXDUMP_CHECK_H

#include <stdio.h>
#include <string.h>

#define CHECK(cond) do { if (!(cond)) { fprintf(stderr, "%s:%d: failed: %s\n", __FILE__, __LINE__, #cond); failures++; } } while (0)
#define CHECK_STR(got, want) do { if ((got) == NULL || strcmp((got), (want)) != 0) { fprintf(stderr, "%s:%d: expected \"%s\", got \"%s\"\n", __FILE__, __LINE__, (want), (got) == NULL ? "(null)" : (got)); failures++; } } while (0)

#endif