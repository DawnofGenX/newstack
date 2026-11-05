#include "textstat/http.h"

#include <arpa/inet.h>
#include <errno.h>
#include <netinet/in.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <sys/types.h>
#include <unistd.h>

#include "textstat/contract.h"

#define TEXTSTAT_MAX_HEADER 8192
#define TEXTSTAT_MAX_BODY 65536
#define TEXTSTAT_READ_TIMEOUT_SECONDS 5

static const char *reason_phrase(int status)
{
    switch (status) {
    case 200: return "OK";
    case 404: return "Not Found";
    case 405: return "Method Not Allowed";
    case 413: return "Payload Too Large";
    case 422: return "Unprocessable Entity";
    default: return "Internal Server Error";
    }
}

/* Reads until the CRLFCRLF that ends the header block. Returns bytes read, or -1. */
static ssize_t read_header(int client, char *buffer, size_t capacity)
{
    size_t used = 0;
    while (used + 1 < capacity) {
        ssize_t got = recv(client, buffer + used, capacity - 1 - used, 0);
        if (got <= 0) {
            return -1;
        }
        used += (size_t)got;
        buffer[used] = '\0';
        char *blank = strstr(buffer, "\r\n\r\n");
        if (blank != NULL) {
            return (ssize_t)(blank - buffer) + 4;
        }
    }
    return -1;
}

static int send_all(int client, const char *data, size_t length)
{
    while (length > 0) {
        ssize_t sent = send(client, data, length, 0);
        if (sent <= 0) {
            if (errno == EINTR) {
                continue;
            }
            return 0;
        }
        data += sent;
        length -= (size_t)sent;
    }
    return 1;
}

static void respond(int client, struct textstat_reply reply)
{
    char header[512];
    size_t length = reply.body != NULL ? strlen(reply.body) : 0;
    int written = snprintf(header, sizeof header,
                           "HTTP/1.1 %d %s\r\n"
                           "Content-Type: application/json\r\n"
                           "Content-Length: %lu\r\n"
                           "Connection: close\r\n\r\n",
                           reply.status, reason_phrase(reply.status),
                           (unsigned long)length);
    if (written > 0) {
        send_all(client, header, (size_t)written);
    }
    if (length > 0) {
        send_all(client, reply.body, length);
    }
}

/* Copies a header value out of the block; returns length or 0. */
static size_t header_value(const char *header, const char *name, char *out, size_t capacity)
{
    size_t name_length = strlen(name);
    const char *cursor = header;
    while ((cursor = strstr(cursor, "\r\n")) != NULL) {
        cursor += 2;
        if (strncasecmp(cursor, name, name_length) == 0 && cursor[name_length] == ':') {
            const char *value = cursor + name_length + 1;
            while (*value == ' ' || *value == '\t') {
                value++;
            }
            const char *end = strstr(value, "\r\n");
            size_t length = end != NULL ? (size_t)(end - value) : strlen(value);
            if (length >= capacity) {
                length = capacity - 1;
            }
            memcpy(out, value, length);
            out[length] = '\0';
            return length;
        }
    }
    return 0;
}

static void handle_client(int client)
{
    char *header = malloc(TEXTSTAT_MAX_HEADER);
    if (header == NULL) {
        return;
    }
    ssize_t header_length = read_header(client, header, TEXTSTAT_MAX_HEADER);
    if (header_length < 0) {
        free(header);
        return;
    }

    char method[16] = {0};
    char target[2048] = {0};
    const char *line_end = strstr(header, "\r\n");
    size_t line_length = line_end != NULL ? (size_t)(line_end - header) : strlen(header);
    if (sscanf(header, "%15s %2047s", method, target) != 2 || line_length == 0) {
        struct textstat_reply bad = {422, NULL};
        bad.body = strdup("{\"error\":\"bad_request\"}");
        respond(client, bad);
        textstat_reply_free(bad);
        free(header);
        return;
    }

    char *query_at = strchr(target, '?');
    const char *query = "";
    if (query_at != NULL) {
        *query_at = '\0';
        query = query_at + 1;
    }

    char length_text[32] = {0};
    size_t declared = 0;
    if (header_value(header, "content-length", length_text, sizeof length_text) > 0) {
        declared = (size_t)strtoul(length_text, NULL, 10);
    }

    char *payload = calloc(1, declared + 1);
    size_t carried = 0;
    if (declared > TEXTSTAT_MAX_BODY) {
        struct textstat_reply too_large = {413, NULL};
        too_large.body = strdup("{\"error\":\"body_too_large\"}");
        respond(client, too_large);
        textstat_reply_free(too_large);
        free(payload);
        free(header);
        return;
    }
    if (payload != NULL) {
        /* Part of the body may already be in the header block. */
        if ((size_t)header_length < TEXTSTAT_MAX_HEADER) {
            const char *extra = header + header_length;
            size_t extra_length = strlen(extra);
            if (extra_length > declared) {
                extra_length = declared;
            }
            memcpy(payload, extra, extra_length);
            carried = extra_length;
        }
        while (carried < declared) {
            ssize_t got = recv(client, payload + carried, declared - carried, 0);
            if (got <= 0) {
                break;
            }
            carried += (size_t)got;
        }
        payload[declared] = '\0';
    }

    struct textstat_reply reply = textstat_route(method, target, query,
                                                 payload != NULL ? payload : "");
    respond(client, reply);
    textstat_reply_free(reply);
    free(payload);
    free(header);
}

int textstat_serve(const char *host, int port)
{
    int listener = socket(AF_INET, SOCK_STREAM, 0);
    if (listener < 0) {
        perror("socket");
        return -1;
    }

    int reuse = 1;
    if (setsockopt(listener, SOL_SOCKET, SO_REUSEADDR, &reuse, sizeof reuse) < 0) {
        perror("setsockopt");
        close(listener);
        return -1;
    }

    struct sockaddr_in address;
    memset(&address, 0, sizeof address);
    address.sin_family = AF_INET;
    address.sin_port = htons((unsigned short)port);
    if (inet_pton(AF_INET, host, &address.sin_addr) != 1) {
        fprintf(stderr, "cannot parse '%s' as an IPv4 address\n", host);
        close(listener);
        return -1;
    }
    if (bind(listener, (struct sockaddr *)&address, sizeof address) < 0) {
        perror("bind");
        close(listener);
        return -1;
    }
    if (listen(listener, 16) < 0) {
        perror("listen");
        close(listener);
        return -1;
    }

    signal(SIGPIPE, SIG_IGN);
    printf("listening on http://%s:%d\n", host, port);
    fflush(stdout);

    for (;;) {
        int client = accept(listener, NULL, NULL);
        if (client < 0) {
            if (errno == EINTR) {
                continue;
            }
            perror("accept");
            break;
        }
        struct timeval timeout;
        timeout.tv_sec = TEXTSTAT_READ_TIMEOUT_SECONDS;
        timeout.tv_usec = 0;
        setsockopt(client, SOL_SOCKET, SO_RCVTIMEO, &timeout, sizeof timeout);
        handle_client(client);
        close(client);
    }
    close(listener);
    return 0;
}
