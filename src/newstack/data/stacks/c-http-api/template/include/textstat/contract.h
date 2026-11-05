#ifndef TEXTSTAT_CONTRACT_H
#define TEXTSTAT_CONTRACT_H

/* One answer: an HTTP status and the JSON body that goes with it. */
struct textstat_reply {
    int status;
    char *body; /* malloc'd; free with textstat_reply_free */
};

/* Routes one request. Pure: no sockets, no globals, no I/O.
 *
 * method is "GET", "POST" or anything else; path has no query string; query is
 * the raw query (with or without a leading '?'); body is the request payload
 * (never NULL - pass "" for none).
 */
struct textstat_reply textstat_route(const char *method, const char *path,
                                     const char *query, const char *body);

void textstat_reply_free(struct textstat_reply reply);

#endif /* TEXTSTAT_CONTRACT_H */
