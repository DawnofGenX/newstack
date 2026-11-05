#include "textstat/json.h"

#include <stdlib.h>
#include <string.h>

#define TEXTSTAT_JSON_MAX_DEPTH 32

struct parser {
    const char *start;
    const char *cursor;
};

/* A growable byte buffer, used for keys and for the text member. */
struct buffer {
    char *data;
    size_t length;
    size_t capacity;
};

static void buffer_init(struct buffer *buffer)
{
    buffer->data = NULL;
    buffer->length = 0;
    buffer->capacity = 0;
}

static void buffer_free(struct buffer *buffer)
{
    free(buffer->data);
    buffer_init(buffer);
}

static int buffer_push(struct buffer *buffer, char byte)
{
    if (buffer->length + 1 >= buffer->capacity) {
        size_t capacity = buffer->capacity ? buffer->capacity * 2 : 32;
        char *grown = realloc(buffer->data, capacity);
        if (grown == NULL) {
            return 0;
        }
        buffer->data = grown;
        buffer->capacity = capacity;
    }
    buffer->data[buffer->length++] = byte;
    buffer->data[buffer->length] = '\0';
    return 1;
}

static int buffer_push_utf8(struct buffer *buffer, unsigned long code)
{
    if (code < 0x80) {
        return buffer_push(buffer, (char)code);
    }
    if (code < 0x800) {
        return buffer_push(buffer, (char)(0xC0 | (code >> 6))) &&
               buffer_push(buffer, (char)(0x80 | (code & 0x3F)));
    }
    if (code < 0x10000) {
        return buffer_push(buffer, (char)(0xE0 | (code >> 12))) &&
               buffer_push(buffer, (char)(0x80 | ((code >> 6) & 0x3F))) &&
               buffer_push(buffer, (char)(0x80 | (code & 0x3F)));
    }
    return buffer_push(buffer, (char)(0xF0 | (code >> 18))) &&
           buffer_push(buffer, (char)(0x80 | ((code >> 12) & 0x3F))) &&
           buffer_push(buffer, (char)(0x80 | ((code >> 6) & 0x3F))) &&
           buffer_push(buffer, (char)(0x80 | (code & 0x3F)));
}

static void skip_whitespace(struct parser *ps)
{
    while (*ps->cursor == ' ' || *ps->cursor == '\t' || *ps->cursor == '\n' ||
           *ps->cursor == '\r') {
        ps->cursor++;
    }
}

static int hex_digit(char character, unsigned *value)
{
    if (character >= '0' && character <= '9') {
        *value = (unsigned)(character - '0');
        return 1;
    }
    if (character >= 'a' && character <= 'f') {
        *value = (unsigned)(character - 'a') + 10;
        return 1;
    }
    if (character >= 'A' && character <= 'F') {
        *value = (unsigned)(character - 'A') + 10;
        return 1;
    }
    return 0;
}

static int read_hex4(struct parser *ps, unsigned *value)
{
    unsigned result = 0;
    for (int index = 0; index < 4; index++) {
        unsigned digit = 0;
        if (!hex_digit(ps->cursor[index], &digit)) {
            return 0;
        }
        result = (result << 4) | digit;
    }
    ps->cursor += 4;
    *value = result;
    return 1;
}

/* Parses a string literal into out (when out is not NULL). */
static int parse_string(struct parser *ps, struct buffer *out)
{
    struct buffer scratch;
    struct buffer *target = out;

    if (out == NULL) {
        buffer_init(&scratch);
        target = &scratch;
    }
    if (*ps->cursor != '"') {
        if (out == NULL) {
            buffer_free(&scratch);
        }
        return 0;
    }
    ps->cursor++;
    for (;;) {
        unsigned char byte = (unsigned char)*ps->cursor;
        if (byte == '\0' || byte < 0x20) {
            if (out == NULL) {
                buffer_free(&scratch);
            }
            return 0;
        }
        if (byte == '"') {
            ps->cursor++;
            break;
        }
        if (byte != '\\') {
            if (!buffer_push(target, (char)byte)) {
                if (out == NULL) {
                    buffer_free(&scratch);
                }
                return 0;
            }
            ps->cursor++;
            continue;
        }
        ps->cursor++;
        switch (*ps->cursor) {
        case '"': if (!buffer_push(target, '"')) { goto fail; } break;
        case '\\': if (!buffer_push(target, '\\')) { goto fail; } break;
        case '/': if (!buffer_push(target, '/')) { goto fail; } break;
        case 'b': if (!buffer_push(target, '\b')) { goto fail; } break;
        case 'f': if (!buffer_push(target, '\f')) { goto fail; } break;
        case 'n': if (!buffer_push(target, '\n')) { goto fail; } break;
        case 'r': if (!buffer_push(target, '\r')) { goto fail; } break;
        case 't': if (!buffer_push(target, '\t')) { goto fail; } break;
        case 'u': {
            unsigned code = 0;
            ps->cursor++;
            if (!read_hex4(ps, &code)) {
                goto fail;
            }
            if (code >= 0xD800 && code <= 0xDBFF && ps->cursor[0] == '\\' &&
                ps->cursor[1] == 'u') {
                const char *save = ps->cursor;
                unsigned low = 0;
                ps->cursor += 2;
                if (read_hex4(ps, &low) && low >= 0xDC00 && low <= 0xDFFF) {
                    unsigned long combined =
                        0x10000UL + (((unsigned long)code - 0xD800UL) << 10) +
                        ((unsigned long)low - 0xDC00UL);
                    if (!buffer_push_utf8(target, combined)) {
                        goto fail;
                    }
                } else {
                    ps->cursor = save;
                    if (!buffer_push_utf8(target, code)) {
                        goto fail;
                    }
                }
            } else if (!buffer_push_utf8(target, code)) {
                goto fail;
            }
            /* the shared ps->cursor++ below steps back over the last hex digit */
            ps->cursor--;
            break;
        }
        default:
            goto fail;
        }
        ps->cursor++;
        continue;
fail:
        if (out == NULL) {
            buffer_free(&scratch);
        }
        return 0;
    }
    if (out == NULL) {
        buffer_free(&scratch);
    }
    return 1;
}

static int parse_number(struct parser *ps)
{
    const char *start = ps->cursor;
    if (*ps->cursor == '-') {
        ps->cursor++;
    }
    if (*ps->cursor == '0') {
        ps->cursor++;
    } else if (*ps->cursor >= '1' && *ps->cursor <= '9') {
        while (*ps->cursor >= '0' && *ps->cursor <= '9') {
            ps->cursor++;
        }
    } else {
        return 0;
    }
    if (*ps->cursor == '.') {
        ps->cursor++;
        if (!(*ps->cursor >= '0' && *ps->cursor <= '9')) {
            return 0;
        }
        while (*ps->cursor >= '0' && *ps->cursor <= '9') {
            ps->cursor++;
        }
    }
    if (*ps->cursor == 'e' || *ps->cursor == 'E') {
        ps->cursor++;
        if (*ps->cursor == '+' || *ps->cursor == '-') {
            ps->cursor++;
        }
        if (!(*ps->cursor >= '0' && *ps->cursor <= '9')) {
            return 0;
        }
        while (*ps->cursor >= '0' && *ps->cursor <= '9') {
            ps->cursor++;
        }
    }
    return ps->cursor > start;
}

static int parse_literal(struct parser *ps, const char *word)
{
    size_t length = strlen(word);
    if (strncmp(ps->cursor, word, length) != 0) {
        return 0;
    }
    ps->cursor += length;
    return 1;
}

static int parse_value(struct parser *ps, int depth);

static int parse_array(struct parser *ps, int depth)
{
    if (*ps->cursor != '[') {
        return 0;
    }
    ps->cursor++;
    skip_whitespace(ps);
    if (*ps->cursor == ']') {
        ps->cursor++;
        return 1;
    }
    for (;;) {
        if (!parse_value(ps, depth + 1)) {
            return 0;
        }
        skip_whitespace(ps);
        if (*ps->cursor == ',') {
            ps->cursor++;
            skip_whitespace(ps);
            continue;
        }
        if (*ps->cursor == ']') {
            ps->cursor++;
            return 1;
        }
        return 0;
    }
}

/* Parses an object. When text is not NULL it receives the "text" member. */
static int parse_object(struct parser *ps, int depth, struct buffer *text, int *text_is_string)
{
    if (*ps->cursor != '{') {
        return 0;
    }
    ps->cursor++;
    skip_whitespace(ps);
    if (*ps->cursor == '}') {
        ps->cursor++;
        return 1;
    }
    for (;;) {
        struct buffer key;
        buffer_init(&key);
        skip_whitespace(ps);
        if (!parse_string(ps, &key)) {
            buffer_free(&key);
            return 0;
        }
        skip_whitespace(ps);
        if (*ps->cursor != ':') {
            buffer_free(&key);
            return 0;
        }
        ps->cursor++;
        skip_whitespace(ps);
        if (text != NULL && strcmp(key.data != NULL ? key.data : "", "text") == 0) {
            if (*ps->cursor == '"' && text_is_string != NULL) {
                if (!parse_string(ps, text)) {
                    buffer_free(&key);
                    return 0;
                }
                *text_is_string = 1;
            } else {
                if (!parse_value(ps, depth + 1)) {
                    buffer_free(&key);
                    return 0;
                }
                *text_is_string = 0;
            }
        } else if (!parse_value(ps, depth + 1)) {
            buffer_free(&key);
            return 0;
        }
        buffer_free(&key);
        skip_whitespace(ps);
        if (*ps->cursor == ',') {
            ps->cursor++;
            continue;
        }
        if (*ps->cursor == '}') {
            ps->cursor++;
            return 1;
        }
        return 0;
    }
}

static int parse_value(struct parser *ps, int depth)
{
    if (depth > TEXTSTAT_JSON_MAX_DEPTH) {
        return 0;
    }
    skip_whitespace(ps);
    switch (*ps->cursor) {
    case '{': return parse_object(ps, depth, NULL, NULL);
    case '[': return parse_array(ps, depth);
    case '"': return parse_string(ps, NULL);
    case 't': return parse_literal(ps, "true");
    case 'f': return parse_literal(ps, "false");
    case 'n': return parse_literal(ps, "null");
    default: return parse_number(ps);
    }
}

enum textstat_json_kind textstat_json_read_text(const char *body, char **out)
{
    struct parser ps;
    struct buffer text;
    int text_is_string = 0;

    if (out != NULL) {
        *out = NULL;
    }
    if (body == NULL) {
        return TEXTSTAT_JSON_INVALID;
    }
    ps.start = body;
    ps.cursor = body;
    buffer_init(&text);
    skip_whitespace(&ps);
    if (*ps.cursor != '{') {
        return TEXTSTAT_JSON_INVALID;
    }
    if (!parse_object(&ps, 0, &text, &text_is_string)) {
        buffer_free(&text);
        return TEXTSTAT_JSON_INVALID;
    }
    skip_whitespace(&ps);
    if (*ps.cursor != '\0') {
        buffer_free(&text);
        return TEXTSTAT_JSON_INVALID;
    }
    if (!text_is_string) {
        buffer_free(&text);
        return TEXTSTAT_JSON_MISSING;
    }
    if (out != NULL) {
        *out = text.data;
    } else {
        buffer_free(&text);
    }
    return TEXTSTAT_JSON_TEXT;
}
