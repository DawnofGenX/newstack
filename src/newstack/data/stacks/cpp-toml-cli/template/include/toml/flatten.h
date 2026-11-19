#ifndef TOML_FLATTEN_H
#define TOML_FLATTEN_H

#include <string>

/* Parse a small TOML subset and return flattened "key = value" lines.
 * Supports [section] headers and key = value pairs (strings, numbers, booleans).
 * Keys are flattened as "section.key = value" (or "key = value" at top level). */
std::string toml_flatten(const std::string &input);

#endif