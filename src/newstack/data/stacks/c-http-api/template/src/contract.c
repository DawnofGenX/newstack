#include "textstat/contract.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "textstat/counters.h"
#include "textstat/json.h"

/* A growable string, so a body never has to guess its final size. */
struct sbuf {
    char *data;
    size_t length;
    size_t capacity;
};

static void sb_init(struct sbuf *sb)
{
    sb->data = NULL;
    sb->length = 0;
    sb->capacity = 0;
}

static int sb_reserve(struct sbuf *sb, size_t extra)
{
    size_t needed = sb->length + extra + 1;
    if (needed <= sb->capacity) {
        return 1;
    }
    size_t capacity = sb->capacity ? sb->capacity : 64;
    while (capacity < needed) {
        capacity *= 2;
    }
    char *grown = realloc(sb->data, capacity);
    if (grown == NULL) {
        return 0;
    }
    sb->data = grown;
    sb->capacity = capacity;
    return 1;
}

static int sb_add(struct sbuf *sb, const char *text)
{
    size_t length = strlen(text);
    if (!sb_reserve(sb, length)) {
        return 0;
    }
    memcpy(sb->data + sb->length, text, length);
    sb->length += length;
    sb->data[sb->length] = '\0';
    return 1;
}

static int sb_add_escaped(struct sbuf *sb, const char *text)
{
    for (const unsigned char *at = (const unsigned char *)text; *at != '\0'; at++) {
        char scratch[8];
        switch (*at) {
        case '"': if (!sb_add(sb, "\\\"")) { return 0; } break;
        case '\\': if (!sb_add(sb, "\\\\")) { return 0; } break;
        case '\n': if (!sb_add(sb, "\\n")) { return 0; } break;
        case '\r': if (!sb_add(sb, "\\r")) { return 0; } break;
        case '\t': if (!sb_add(sb, "\\t")) { return 0; } break;
        case '\b': if (!sb_add(sb, "\\b")) { return 0; } break;
        case '\f': if (!sb_add(sb, "\\f")) { return 0; } break;
        default:
            if (*at < 0x20) {
                snprintf(scratch, sizeof scratch, "\\u%04x", (unsigned)*at);
                if (!sb_add(sb, scratch)) {
                    return 0;
                }
            } else {
                scratch[0] = (char)*at;
                scratch[1] = '\0';
                if (!sb_add(sb, scratch)) {
                    return 0;
                }
            }
            break;
        }
    }
    return 1;
}

static struct textstat_reply reply_of(int status, struct sbuf *sb)
{
    struct textstat_reply reply;
    reply.status = status;
    if (sb->data == NULL) {
        reply.body = calloc(1, 1);
    } else {
        reply.body = sb->data;
    }
    return reply;
}

void textstat_reply_free(struct textstat_reply reply)
{
    free(reply.body);
}

static struct textstat_reply error_reply(int status, const char *code, const char *detail)
{
    struct sbuf sb;
    sb_init(&sb);
    sb_add(&sb, "{\"error\":\"");
    sb_add(&sb, code);
    sb_add(&sb, "\"");
    if (detail != NULL) {
        sb_add(&sb, ",\"detail\":\"");
        sb_add_escaped(&sb, detail);
        sb_add(&sb, "\"");
    }
    sb_add(&sb, "}");
    return reply_of(status, &sb);
}

static struct textstat_reply counts_reply(const char *text)
{
    struct textstat_counts counts = textstat_count(text, strlen(text));
    char numbers[128];
    struct sbuf sb;
    sb_init(&sb);
    sb_add(&sb, "{\"text\":\"");
    sb_add_escaped(&sb, text);
    snprintf(numbers, sizeof numbers, "\",\"lines\":%lu,\"words\":%lu,\"bytes\":%lu}",
             (unsigned long)counts.lines, (unsigned long)counts.words,
             (unsigned long)counts.bytes);
    sb_add(&sb, numbers);
    return reply_of(200, &sb);
}

static int hex_value(char character)
{
    if (character >= '0' && character <= '9') {
        return character - '0';
    }
    if (character >= 'a' && character <= 'f') {
        return character - 'a' + 10;
    }
    if (character >= 'A' && character <= 'F') {
        return character - 'A' + 10;
    }
    return -1;
}

/* Percent-decodes one query value; '+' means a space. Returns malloc'd text. */
static char *decode_value(const char *value, size_t length)
{
    char *out = malloc(length + 1);
    size_t written = 0;
    if (out == NULL) {
        return NULL;
    }
    for (size_t index = 0; index < length; index++) {
        char character = value[index];
        if (character == '+') {
            out[written++] = ' ';
        } else if (character == '%' && index + 2 < length) {
            int high = hex_value(value[index + 1]);
            int low = hex_value(value[index + 2]);
            if (high >= 0 && low >= 0) {
                out[written++] = (char)((high << 4) | low);
                index += 2;
            } else {
                out[written++] = character;
            }
        } else {
            out[written++] = character;
        }
    }
    out[written] = '\0';
    return out;
}

/* The first value for name in a raw query string, or NULL. */
static char *query_param(const char *query, const char *name)
{
    size_t name_length = strlen(name);
    const char *cursor = query;
    if (*cursor == '?') {
        cursor++;
    }
    while (*cursor != '\0') {
        const char *pair_end = strchr(cursor, '&');
        size_t pair_length = pair_end ? (size_t)(pair_end - cursor) : strlen(cursor);
        const char *equals = memchr(cursor, '=', pair_length);
        if (equals != NULL) {
            size_t key_length = (size_t)(equals - cursor);
            if (key_length == name_length &&
                strncmp(cursor, name, name_length) == 0) {
                return decode_value(equals + 1, pair_length - key_length - 1);
            }
        }
        if (pair_end == NULL) {
            break;
        }
        cursor = pair_end + 1;
    }
    return NULL;
}

static int is_known_path(const char *path)
{
    return strcmp(path, "/health") == 0 || strcmp(path, "/stats") == 0;
}

struct textstat_reply textstat_route(const char *method, const char *path,
                                     const char *query, const char *body)
{
    const char *verb = method != NULL ? method : "";
    const char *target = path != NULL ? path : "/";
    const char *raw_query = query != NULL ? query : "";
    const char *payload = body != NULL ? body : "";

    if (strcmp(verb, "GET") == 0 && strcmp(target, "/health") == 0) {
        struct sbuf sb;
        sb_init(&sb);
        sb_add(&sb, "{\"status\":\"ok\"}");
        return reply_of(200, &sb);
    }
    if (strcmp(verb, "GET") == 0 && strcmp(target, "/stats") == 0) {
        char *text = query_param(raw_query, "text");
        if (text == NULL) {
            return error_reply(422, "missing_text", NULL);
        }
        struct textstat_reply reply = counts_reply(text);
        free(text);
        return reply;
    }
    if (strcmp(verb, "POST") == 0 && strcmp(target, "/stats") == 0) {
        char *text = NULL;
        switch (textstat_json_read_text(payload, &text)) {
        case TEXTSTAT_JSON_TEXT: {
            struct textstat_reply reply = counts_reply(text);
            free(text);
            return reply;
        }
        case TEXTSTAT_JSON_MISSING:
            return error_reply(422, "missing_text", NULL);
        case TEXTSTAT_JSON_INVALID:
        default:
            return error_reply(422, "invalid_json", NULL);
        }
    }
    if (is_known_path(target)) {
        return error_reply(405, "method_not_allowed", NULL);
    }
    {
        struct sbuf detail;
        sb_init(&detail);
        sb_add(&detail, "no route for ");
        sb_add(&detail, verb);
        sb_add(&detail, " ");
        sb_add(&detail, target);
        struct textstat_reply reply = error_reply(404, "not_found", detail.data);
        free(detail.data);
        return reply;
    }
}
