# The whole HTTP contract lives here as a pure function, so it can be unit
# tested without binding a socket. plumber.R only translates between the
# request object and route().

# A reply is list(status = integer, body = list). Every branch returns JSON:
# an error body is list(error = "code", detail = "explanation").
textstat_reply <- function(status, body) {
  list(status = as.integer(status), body = body)
}

textstat_error <- function(status, code, detail = NULL) {
  body <- list(error = code)
  if (!is.null(detail)) {
    body$detail <- detail
  }
  textstat_reply(status, body)
}

# Reads one query-string parameter, decoding percent escapes. Returns NULL when
# the parameter is absent, which is how GET /stats tells "missing" from "".
textstat_query_param <- function(query, name) {
  if (is.null(query) || !nzchar(query)) {
    return(NULL)
  }
  # plumber hands over the raw query string with its "?" still attached, so
  # strip it here and the function works with or without it.
  query <- sub("^\\?", "", query)
  if (!nzchar(query)) {
    return(NULL)
  }
  for (pair in strsplit(query, "&", fixed = TRUE)[[1]]) {
    bits <- strsplit(pair, "=", fixed = TRUE)[[1]]
    if (identical(utils::URLdecode(bits[1]), name)) {
      value <- if (length(bits) > 1L) paste(bits[-1], collapse = "=") else ""
      return(utils::URLdecode(value))
    }
  }
  NULL
}

# Routes one request. `body` is the raw request body for POST /stats.
#
# @param method the HTTP method, in any case
# @param path   the request path
# @param query  the raw query string, without the leading "?"
# @param body   the raw body, or NULL
# @return list(status = integer, body = list)
textstat_route <- function(method, path, query = NULL, body = NULL) {
  method <- toupper(method)
  known <- path %in% c("/health", "/stats")

  if (identical(path, "/health") && identical(method, "GET")) {
    return(textstat_reply(200L, list(status = "ok")))
  }
  if (identical(path, "/stats") && identical(method, "GET")) {
    text <- textstat_query_param(query, "text")
    if (is.null(text)) {
      return(textstat_error(422L, "missing_text"))
    }
    return(textstat_reply(200L, textstat_payload(text)))
  }
  if (identical(path, "/stats") && identical(method, "POST")) {
    parsed <- tryCatch(
      jsonlite::fromJSON(if (is.null(body)) "" else body, simplifyVector = TRUE),
      error = function(e) NULL
    )
    if (is.null(parsed)) {
      return(textstat_error(422L, "invalid_json"))
    }
    text <- if (is.list(parsed)) parsed[["text"]] else NULL
    if (!is.character(text) || length(text) != 1L) {
      return(textstat_error(422L, "missing_text"))
    }
    return(textstat_reply(200L, textstat_payload(text)))
  }
  if (known) {
    return(textstat_error(405L, "method_not_allowed"))
  }
  textstat_error(404L, "not_found", paste("no route for", method, path))
}
