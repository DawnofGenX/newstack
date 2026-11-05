# The route table. plumber reads these annotations when pr() is called, so the
# file is the API document as well as the server: every route below is answered
# by textstat_route(), which keeps the contract testable without a socket.

source("R/counts.R")
source("R/contract.R")

# Turns a textstat_route() reply into a plumber response. Returning the body
# last means the default JSON serializer writes it.
respond <- function(res, reply) {
  res$status <- reply$status
  res$setHeader("content-type", "application/json")
  reply$body
}

#* Health probe
#* @get /health
function(res) {
  respond(res, textstat_route("GET", "/health"))
}

#* Count the text passed as ?text=
#* @param text:string the text to count
#* @get /stats
function(req, res) {
  respond(res, textstat_route("GET", "/stats", req$QUERY_STRING))
}

#* Count the text sent as {"text": "..."}
#* @post /stats
function(req, res) {
  respond(res, textstat_route("POST", "/stats", req$QUERY_STRING, req$postBody))
}
