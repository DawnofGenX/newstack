#!/usr/bin/env Rscript
# Starts the service. PORT selects the port (8080 by default) and HOST the
# interface to bind (127.0.0.1 by default), so the same file works locally and
# in CI.
#
#   Rscript bin/serve.R
#   PORT=5423 Rscript bin/serve.R

args <- commandArgs(trailingOnly = FALSE)
file_arg <- grep("^--file=", args, value = TRUE)
this_file <- if (length(file_arg) >= 1) sub("^--file=", "", file_arg[1]) else args[2]
root <- normalizePath(file.path(dirname(normalizePath(this_file, mustWork = FALSE)), ".."), mustWork = FALSE)
setwd(root)

port <- suppressWarnings(as.integer(Sys.getenv("PORT", "8080")))
if (is.na(port)) {
  stop("PORT must be a number", call. = FALSE)
}
host <- Sys.getenv("HOST", "127.0.0.1")

# Unknown paths must answer JSON, not plumber's default HTML error page.
not_found <- function(req, res) {
  res$status <- 404L
  res$setHeader("content-type", "application/json")
  detail <- paste("no route for", req$REQUEST_METHOD, req$PATH_INFO)
  list(error = "not_found", detail = detail)
}

app <- plumber::pr("plumber.R")
app <- plumber::pr_set_404(app, not_found)
# Scalars stay scalars: plumber's default JSON serializer turns every element
# of a list into a one-element array ({"lines":[2]}).
app <- plumber::pr_set_serializer(app, plumber::serializer_unboxed_json())
# Leave the body alone: the JSON parser answers 500 on a malformed body, while
# textstat_route() answers 422 invalid_json, which is the contract.
app <- plumber::pr_set_parsers(app, c("form", "text", "octet"))
plumber::pr_run(app, host = host, port = port, quiet = TRUE)
