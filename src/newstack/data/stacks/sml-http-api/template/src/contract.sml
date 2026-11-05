(* The HTTP contract with no socket in sight: four strings in, status and body
   out. Every status code can be tested without binding a port. *)
structure Contract = struct
  type reply = {status : int, body : string}

  fun reply (status, body) : reply = {status = status, body = body}

  fun hexVal c =
      if Char.isDigit c then ord c - ord #"0"
      else if c >= #"a" andalso c <= #"f" then ord c - ord #"a" + 10
      else if c >= #"A" andalso c <= #"F" then ord c - ord #"A" + 10
      else ~1

  (*| Quote a string for JSON, escaping only what JSON requires. Bytes above
     ASCII pass through: they are already UTF-8 here. *)
  fun jsonQuote (value : string) : string =
      let
        val pieces = ref ["\""]
        val () = CharVector.app
                   (fn c =>
                       let val code = ord c
                           val piece =
                               if c = #"\"" then "\\\""
                               else if c = #"\\" then "\\\\"
                               else if c = #"\n" then "\\n"
                               else if c = #"\r" then "\\r"
                               else if c = #"\t" then "\\t"
                               else if c = #"\008" then "\\b"
                               else if c = #"\012" then "\\f"
                               else if code < 0x20 then
                                 let
                                   val hex = Int.fmt StringCvt.HEX code
                                 in
                                   "\\u00" ^ (if String.size hex = 1 then "0" ^ hex else hex)
                                 end
                               else String.str c
                       in
                         pieces := piece :: !pieces
                       end)
                   value
        val () = pieces := "\"" :: !pieces
      in
        String.concat (List.rev (!pieces))
      end

  (*| Percent-decode a query value: '+' is a space, and %XX is a byte, so
     %C3%A9 is one character and not two. *)
  fun percentDecode (raw : string) : string =
      let
        val out = ref []
        val n = String.size raw
        fun at i = if i < n then SOME (String.sub (raw, i)) else NONE
        fun loop i =
            if i >= n then ()
            else
              let val c = String.sub (raw, i) in
                if c = #"%" then
                  (case (at (i + 1), at (i + 2)) of
                       (SOME hi, SOME lo) =>
                         let val h = hexVal hi val l = hexVal lo in
                           if h >= 0 andalso l >= 0 then
                             (out := String.str (Char.chr (h * 16 + l)) :: !out; loop (i + 3))
                           else (out := "%" :: !out; loop (i + 1))
                         end
                     | _ => (out := "%" :: !out; loop (i + 1)))
                else if c = #"+" then (out := " " :: !out; loop (i + 1))
                else (out := String.str c :: !out; loop (i + 1))
              end
        val () = loop 0
      in
        String.concat (List.rev (!out))
      end

  (*| Query parameters, first occurrence winning, a leading '?' dropped. *)
  fun queryParams (query : string) : (string * string) list =
      let
        val raw =
            if String.size query > 0 andalso String.sub (query, 0) = #"?"
            then String.extract (query, 1, NONE)
            else query
        val pairs = String.fields (fn c => c = #"&") raw
        fun splitFirst pair =
            let
              val n = String.size pair
              fun find i =
                  if i >= n then NONE
                  else if String.sub (pair, i) = #"=" then SOME i
                  else find (i + 1)
            in
              case find 0 of
                  NONE => (pair, "")
                | SOME i => (String.substring (pair, 0, i),
                             String.extract (pair, i + 1, NONE))
            end
        fun add (pair, acc) =
            if pair = "" then acc
            else
              let
                val (name, value) = splitFirst pair
                val decodedName = percentDecode name
                val decodedValue = percentDecode value
              in
                if List.exists (fn (k, _) => k = decodedName) acc then acc
                else acc @ [(decodedName, decodedValue)]
              end
      in
        List.foldl add [] pairs
      end

  fun statsJson (text : string) : string =
      let val c = Counts.count text in
        "{\"text\":" ^ jsonQuote text
        ^ ",\"lines\":" ^ Int.toString (#lines c)
        ^ ",\"words\":" ^ Int.toString (#words c)
        ^ ",\"bytes\":" ^ Int.toString (#bytes c) ^ "}"
      end

  fun error (status, code) = reply (status, "{\"error\":" ^ jsonQuote code ^ "}")

  fun errorDetail (status, code, detail) =
      reply (status,
             "{\"error\":" ^ jsonQuote code ^ ",\"detail\":" ^ jsonQuote detail ^ "}")

  (*| method, path, query, body -> status and JSON body. *)
  fun route {method, path, query, body} : reply =
      if method = "GET" andalso path = "/health" then
        reply (200, "{\"status\":\"ok\"}")
      else if method = "GET" andalso path = "/stats" then
        (case List.find (fn (k, _) => k = "text") (queryParams query) of
             NONE => error (422, "missing_text")
           | SOME (_, text) => reply (200, statsJson text))
      else if method = "POST" andalso path = "/stats" then
        (case Json.readBody body of
             Json.Text text => reply (200, statsJson text)
           | Json.Missing => error (422, "missing_text")
           | Json.Invalid => error (422, "invalid_json"))
      else if path = "/health" orelse path = "/stats" then
        error (405, "method_not_allowed")
      else
        errorDetail (404, "not_found", "no route for " ^ method ^ " " ^ path)
end
