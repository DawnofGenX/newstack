#ifndef TEXTSTAT_JSON_H
#define TEXTSTAT_JSON_H

#include <stddef.h>

/* What a JSON object's "text" member turned out to be. */
enum textstat_json_kind {
    TEXTSTAT_JSON_INVALID = -1, /* the body is not a JSON object at all */
    TEXTSTAT_JSON_MISSING = 0,  /* valid object, but "text" is absent or not a string */
    TEXTSTAT_JSON_TEXT = 1      /* "text" is a string; *out receives it */
};

/* Reads {"text": "..."} out of body.
 *
 * Returns TEXTSTAT_JSON_TEXT and sets *out to a malloc'd, unescaped copy of the
 * string when the member is a JSON string. A number, null, array or object in
 * that position is TEXTSTAT_JSON_MISSING, exactly like an absent member, because
 * the service only ever counts text. Anything that is not a JSON object is
 * TEXTSTAT_JSON_INVALID.
 */
enum textstat_json_kind textstat_json_read_text(const char *body, char **out);

#endif /* TEXTSTAT_JSON_H */
