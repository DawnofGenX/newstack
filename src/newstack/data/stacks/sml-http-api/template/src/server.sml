(* The only file that knows about sockets: read a request off the wire, hand
   four strings to the contract, write the reply back. *)
structure Server = struct
  val maxHead = 16384
  val maxBody = 65536

  fun isCrLf (bytes, i) =
      Word8Vector.sub (bytes, i) = 0w13
      andalso Word8Vector.sub (bytes, i + 1) = 0w10
      andalso Word8Vector.sub (bytes, i + 2) = 0w13
      andalso Word8Vector.sub (bytes, i + 3) = 0w10

  (* Read one byte at a time until the blank line that ends the head. *)
  fun readHead conn =
      let
        val buf = ref (Byte.stringToBytes "")
        val done = ref false
        val count = ref 0
      in
        while not (!done) andalso !count < maxHead do
          let val chunk = Socket.recvVec (conn, 1) in
            if Word8Vector.length chunk = 0 then done := true
            else
              let
                val () = buf := Word8Vector.concat [!buf, chunk]
                val () = count := !count + 1
              in
                if !count >= 4 andalso isCrLf (!buf, !count - 4) then done := true
                else ()
              end
          end;
        {bytes = !buf, complete = !count >= 4 andalso isCrLf (!buf, !count - 4)}
      end

  fun readBodyBytes (conn, length) =
      let
        val buf = ref (Byte.stringToBytes "")
        val open_ = ref true
      in
        while !open_ andalso Word8Vector.length (!buf) < length do
          let val chunk = Socket.recvVec (conn, length - Word8Vector.length (!buf)) in
            if Word8Vector.length chunk = 0 then open_ := false
            else buf := Word8Vector.concat [!buf, chunk]
          end;
        !buf
      end

  fun sendAll (conn, bytes) =
      let
        fun loop slice =
            if Word8VectorSlice.length slice = 0 then ()
            else
              let val sent = Socket.sendVec (conn, slice) in
                if sent <= 0 then ()
                else loop (Word8VectorSlice.subslice (slice, sent, NONE))
              end
      in
        loop (Word8VectorSlice.full bytes)
      end

  fun reason 200 = "OK"
    | reason 400 = "Bad Request"
    | reason 404 = "Not Found"
    | reason 405 = "Method Not Allowed"
    | reason 413 = "Payload Too Large"
    | reason 422 = "Unprocessable Entity"
    | reason _ = "Internal Server Error"

  fun sendReply (conn, status, body) =
      let
        val payload = Byte.stringToBytes body
        val head =
            "HTTP/1.1 " ^ Int.toString status ^ " " ^ reason status ^ "\r\n"
            ^ "content-type: application/json\r\n"
            ^ "content-length: " ^ Int.toString (Word8Vector.length payload) ^ "\r\n"
            ^ "connection: close\r\n\r\n"
      in
        sendAll (conn, Word8Vector.concat [Byte.stringToBytes head, payload])
      end

  fun words (line : string) =
      List.filter (fn w => w <> "") (String.fields (fn c => c = #" ") line)

  fun trim (s : string) =
      let
        val n = String.size s
        fun isBlank c = c = #" " orelse c = #"\t"
        fun left i = if i < n andalso isBlank (String.sub (s, i)) then left (i + 1) else i
        fun right i = if i > 0 andalso isBlank (String.sub (s, i - 1)) then right (i - 1) else i
        val a = left 0
        val b = right n
      in
        if b <= a then "" else String.substring (s, a, b - a)
      end

  fun headerValue (lines, wanted) =
      let
        fun pick (line, best) =
            let
              val n = String.size line
              fun find i = if i >= n then NONE
                           else if String.sub (line, i) = #":" then SOME i
                           else find (i + 1)
            in
              case find 0 of
                  NONE => best
                | SOME i =>
                    if String.map Char.toLower (String.substring (line, 0, i)) = wanted
                    then SOME (trim (String.extract (line, i + 1, NONE)))
                    else best
            end
      in
        List.foldl pick NONE lines
      end

  fun parseIntOpt (s : string) =
      let
        val n = String.size s
        fun go i acc =
            if i >= n then SOME acc
            else if Char.isDigit (String.sub (s, i))
            then go (i + 1) (acc * 10 + (ord (String.sub (s, i)) - ord #"0"))
            else NONE
      in
        if n = 0 then NONE else go 0 0
      end

  fun handleConn conn =
      let
        val head = readHead conn
      in
        if not (#complete head) then sendReply (conn, 400, "{\"error\":\"invalid_json\"}")
        else
          let
            val text = Byte.bytesToString (#bytes head)
            val lines = String.fields (fn c => c = #"\n") text
            val lines = List.map (fn l => if String.isSuffix "\r" l
                                          then String.substring (l, 0, String.size l - 1)
                                          else l) lines
            val (requestLine, headers) =
                case lines of
                    [] => ("", [])
                  | first :: rest => (first, rest)
            val parts = words requestLine
          in
            if List.length parts < 2 then sendReply (conn, 400, "{\"error\":\"invalid_json\"}")
            else
              let
                val method = List.nth (parts, 0)
                val target = List.nth (parts, 1)
                val length =
                    case headerValue (headers, "content-length") of
                        NONE => 0
                      | SOME raw => (case parseIntOpt raw of SOME n => n | NONE => 0)
              in
                if length > maxBody then sendReply (conn, 413, "{\"error\":\"body_too_large\"}")
                else
                  let
                    val bodyBytes = readBodyBytes (conn, length)
                    val payload =
                        if Word8Vector.length bodyBytes = 0 then ""
                        else Byte.bytesToString bodyBytes
                    val (path, query) =
                        case String.fields (fn c => c = #"?") target of
                            [p] => (p, "")
                          | p :: rest => (p, String.concatWith "?" rest)
                          | [] => ("", "")
                    val {status, body} =
                        Contract.route {method = method, path = path,
                                        query = query, body = payload}
                  in
                    sendReply (conn, status, body)
                  end
              end
          end
      end

  fun serve (host : string, port : int) =
      let
        val listener : Socket.passive INetSock.stream_sock = INetSock.TCP.socket ()
        val () = Socket.Ctl.setREUSEADDR (listener, true)
        val () = case NetHostDB.fromString host of
                     SOME inet => Socket.bind (listener, INetSock.toAddr (inet, port))
                   | NONE => raise Fail ("cannot resolve host " ^ host)
        val () = Socket.listen (listener, 16)
      in
        print ("listening on http://" ^ host ^ ":" ^ Int.toString port ^ "\n");
        while true do
          let
            val (conn, _) = Socket.accept listener
          in
            (handleConn conn handle _ => ());
            Socket.close conn
          end
      end
end
