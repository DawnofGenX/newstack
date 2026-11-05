#ifndef TEXTSTAT_HTTP_H
#define TEXTSTAT_HTTP_H

/* Binds host:port and answers requests until the process is killed.
 * Returns 0 if it ever stops, -1 when the socket cannot be opened.
 */
int textstat_serve(const char *host, int port);

#endif /* TEXTSTAT_HTTP_H */
