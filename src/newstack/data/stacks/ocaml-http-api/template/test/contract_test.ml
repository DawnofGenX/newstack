let () =
  let open Harness in
  let route = Contract.route in
  let body_of method_ path query body = (route method_ path query body).Contract.body in
  let status_of method_ path query body = (route method_ path query body).Contract.status in

  check_eq "health" "{\"status\":\"ok\"}" (body_of "GET" "/health" "" "");
  check_eq "get stats" 200 (status_of "GET" "/stats" "text=hello%20world%0A" "");
  check_eq "get body"
    "{\"text\":\"hello world\\n\",\"lines\":1,\"words\":2,\"bytes\":12}"
    (body_of "GET" "/stats" "text=hello%20world%0A" "");
  check_eq "post stats"
    "{\"text\":\"a b\\nc\\n\",\"lines\":2,\"words\":3,\"bytes\":6}"
    (body_of "POST" "/stats" "" "{\"text\": \"a b\\nc\\n\"}");
  check_eq "empty text" "{\"text\":\"\",\"lines\":0,\"words\":0,\"bytes\":0}"
    (body_of "GET" "/stats" "text=" "");
  check_eq "missing query" 422 (status_of "GET" "/stats" "" "");
  check_eq "missing field" 422 (status_of "POST" "/stats" "" "{}");
  check_eq "broken body" 422 (status_of "POST" "/stats" "" "nope");
  check_eq "number field" 422 (status_of "POST" "/stats" "" "{\"text\": 42}");
  check_eq "wrong method health" 405 (status_of "DELETE" "/health" "" "");
  check_eq "wrong method stats" 405 (status_of "PUT" "/stats" "text=a" "");
  check_eq "unknown route" 404 (status_of "GET" "/nope" "" "");
  check_eq "unknown route body"
    "{\"error\":\"not_found\",\"detail\":\"no route for GET /nope\"}"
    (body_of "GET" "/nope" "" "");
  check_eq "second param" "{\"text\":\"hi\",\"lines\":0,\"words\":1,\"bytes\":2}"
    (body_of "GET" "/stats" "other=1&text=hi" "");
  check_eq "plus is space" "{\"text\":\"a b\",\"lines\":0,\"words\":2,\"bytes\":3}"
    (body_of "GET" "/stats" "text=a+b" "");
  finish ()
