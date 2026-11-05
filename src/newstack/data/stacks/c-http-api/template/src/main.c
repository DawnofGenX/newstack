#include <stdio.h>
#include <stdlib.h>

#include "textstat/http.h"

int main(void)
{
    const char *host = getenv("HOST");
    const char *port_text = getenv("PORT");
    int port = 8080;

    if (host == NULL || *host == '\0') {
        host = "127.0.0.1";
    }
    if (port_text != NULL && *port_text != '\0') {
        port = atoi(port_text);
    }
    if (port <= 0 || port > 65535) {
        fprintf(stderr, "PORT must be between 1 and 65535, got '%s'\n", port_text);
        return 2;
    }
    return textstat_serve(host, port) == 0 ? 0 : 1;
}
