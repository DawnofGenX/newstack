(* A strict JSON reader. The SML Basis ships no JSON, so this is a small
   recursive-descent parser: it validates the whole document, keeps a string
   apart from a number, and decodes \u escapes (including surrogate pairs) into
   UTF-8 bytes. *)
structure Json = struct
  datatype value =
      VObj of (string * value) list
    | VArr of value list
    | VStr of string
    | VNum
    | VBool of bool
    | VNull

  (* What a request body turned out to be. *)
  datatype body = Text of string | Missing | Invalid

  exception Bad

  fun peek (src, i) = if i < String.size src then SOME (String.sub (src, i)) else NONE

  fun isWs c = c = #" " orelse c = #"\t" orelse c = #"\n" orelse c = #"\r"

  fun skipWs (src, pos) =
      case peek (src, !pos) of
          SOME c => if isWs c then (pos := !pos + 1; skipWs (src, pos)) else ()
        | NONE => ()

  fun hexVal c =
      if Char.isDigit c then ord c - ord #"0"
      else if c >= #"a" andalso c <= #"f" then ord c - ord #"a" + 10
      else if c >= #"A" andalso c <= #"F" then ord c - ord #"A" + 10
      else raise Bad

  fun readHex4 (src, pos) =
      let
        fun go k acc =
            if k = 4 then acc
            else
              case peek (src, !pos) of
                  SOME c => (pos := !pos + 1; go (k + 1) (acc * 16 + hexVal c))
                | NONE => raise Bad
      in
        go 0 0
      end

  fun utf8 code =
      if code < 0x80 then String.str (Char.chr code)
      else if code < 0x800 then
        String.implode
          [Char.chr (0xC0 + code div 0x40),
           Char.chr (0x80 + code mod 0x40)]
      else if code < 0x10000 then
        String.implode
          [Char.chr (0xE0 + code div 0x1000),
           Char.chr (0x80 + (code div 0x40) mod 0x40),
           Char.chr (0x80 + code mod 0x40)]
      else
        String.implode
          [Char.chr (0xF0 + code div 0x40000),
           Char.chr (0x80 + (code div 0x1000) mod 0x40),
           Char.chr (0x80 + (code div 0x40) mod 0x40),
           Char.chr (0x80 + code mod 0x40)]

  fun expectToken (src, pos, word) =
      let
        val n = String.size word
        fun go k =
            if k = n then pos := !pos + n
            else case peek (src, !pos + k) of
                     SOME c => if c = String.sub (word, k) then go (k + 1) else raise Bad
                   | NONE => raise Bad
      in
        go 0
      end

  fun parseString (src, pos) =
      let
        val () = case peek (src, !pos) of
                     SOME #"\"" => pos := !pos + 1
                   | _ => raise Bad
        fun loop acc =
            case peek (src, !pos) of
                NONE => raise Bad
              | SOME #"\"" => (pos := !pos + 1; String.concat (List.rev acc))
              | SOME #"\\" =>
                  let
                    val () = pos := !pos + 1
                  in
                    case peek (src, !pos) of
                        SOME #"\"" => (pos := !pos + 1; loop ("\"" :: acc))
                      | SOME #"\\" => (pos := !pos + 1; loop ("\\" :: acc))
                      | SOME #"/" => (pos := !pos + 1; loop ("/" :: acc))
                      | SOME #"b" => (pos := !pos + 1; loop ("\008" :: acc))
                      | SOME #"f" => (pos := !pos + 1; loop ("\012" :: acc))
                      | SOME #"n" => (pos := !pos + 1; loop ("\n" :: acc))
                      | SOME #"r" => (pos := !pos + 1; loop ("\r" :: acc))
                      | SOME #"t" => (pos := !pos + 1; loop ("\t" :: acc))
                      | SOME #"u" =>
                          let
                            val () = pos := !pos + 1
                            val hi = readHex4 (src, pos)
                          in
                            if hi >= 0xD800 andalso hi <= 0xDBFF then
                              let
                                val () = case peek (src, !pos) of
                                             SOME #"\\" => pos := !pos + 1
                                           | _ => raise Bad
                                val () = case peek (src, !pos) of
                                             SOME #"u" => pos := !pos + 1
                                           | _ => raise Bad
                                val lo = readHex4 (src, pos)
                              in
                                if lo >= 0xDC00 andalso lo <= 0xDFFF then
                                  loop
                                    (utf8 (0x10000
                                           + (hi - 0xD800) * 0x400
                                           + (lo - 0xDC00)) :: acc)
                                else raise Bad
                              end
                            else loop (utf8 hi :: acc)
                          end
                      | _ => raise Bad
                  end
              | SOME c => (pos := !pos + 1; loop (String.str c :: acc))
      in
        loop []
      end

  fun parseNumber (src, pos) =
      let
        fun digits () =
            case peek (src, !pos) of
                SOME c => if Char.isDigit c then (pos := !pos + 1; digits ()) else ()
              | NONE => ()
        fun needDigit () =
            case peek (src, !pos) of
                SOME c => if Char.isDigit c then (pos := !pos + 1; digits ()) else raise Bad
              | NONE => raise Bad
        val () = case peek (src, !pos) of
                     SOME #"-" => pos := !pos + 1
                   | _ => ()
        val () = case peek (src, !pos) of
                     SOME #"0" => pos := !pos + 1
                   | SOME c => if Char.isDigit c then (pos := !pos + 1; digits ()) else raise Bad
                   | NONE => raise Bad
        val () = case peek (src, !pos) of
                     SOME #"." => (pos := !pos + 1; needDigit ())
                   | _ => ()
        val () = case peek (src, !pos) of
                     SOME c =>
                       if c = #"e" orelse c = #"E" then
                         (pos := !pos + 1;
                          (case peek (src, !pos) of
                               SOME #"+" => pos := !pos + 1
                             | SOME #"-" => pos := !pos + 1
                             | _ => ());
                          needDigit ())
                       else ()
                   | NONE => ()
      in
        ()
      end

  fun parseArray (src, pos) =
      let
        val () = pos := !pos + 1
        val () = skipWs (src, pos)
      in
        case peek (src, !pos) of
            SOME #"]" => (pos := !pos + 1; VArr [])
          | _ =>
              let
                fun items acc =
                    let val v = parseValue (src, pos)
                        val () = skipWs (src, pos)
                    in
                      case peek (src, !pos) of
                          SOME #"," => (pos := !pos + 1; items (v :: acc))
                        | SOME #"]" => (pos := !pos + 1; VArr (List.rev (v :: acc)))
                        | _ => raise Bad
                    end
              in
                items []
              end
      end

  and parseObject (src, pos) =
      let
        val () = pos := !pos + 1
        val () = skipWs (src, pos)
      in
        case peek (src, !pos) of
            SOME #"}" => (pos := !pos + 1; VObj [])
          | _ =>
              let
                fun members acc =
                    let
                      val () = skipWs (src, pos)
                      val key = parseString (src, pos)
                      val () = skipWs (src, pos)
                      val () = case peek (src, !pos) of
                                   SOME #":" => pos := !pos + 1
                                 | _ => raise Bad
                      val value = parseValue (src, pos)
                      val () = skipWs (src, pos)
                    in
                      case peek (src, !pos) of
                          SOME #"," => (pos := !pos + 1; members ((key, value) :: acc))
                        | SOME #"}" =>
                            (pos := !pos + 1; VObj (List.rev ((key, value) :: acc)))
                        | _ => raise Bad
                    end
              in
                members []
              end
      end

  and parseValue (src, pos) =
      let
        val () = skipWs (src, pos)
      in
        case peek (src, !pos) of
            NONE => raise Bad
          | SOME #"{" => parseObject (src, pos)
          | SOME #"[" => parseArray (src, pos)
          | SOME #"\"" => VStr (parseString (src, pos))
          | SOME #"t" => (expectToken (src, pos, "true"); VBool true)
          | SOME #"f" => (expectToken (src, pos, "false"); VBool false)
          | SOME #"n" => (expectToken (src, pos, "null"); VNull)
          | SOME c =>
              if c = #"-" orelse Char.isDigit c then (parseNumber (src, pos); VNum)
              else raise Bad
      end

  (*| Parse a whole document, or NONE when it is not JSON. *)
  fun parse (src : string) : value option =
      let
        val pos = ref 0
        val v = parseValue (src, pos)
        val () = skipWs (src, pos)
      in
        if !pos = String.size src then SOME v else NONE
      end
      handle Bad => NONE
           | _ => NONE

  (*| What a request body says: text, no string "text", or not JSON at all. *)
  fun readBody (raw : string) : body =
      case parse raw of
          NONE => Invalid
        | SOME (VObj fields) =>
            (* a later "text" wins, the way filling a map left to right does *)
            (case List.find (fn (k, _) => k = "text") (List.rev fields) of
                 SOME (_, VStr s) => Text s
               | _ => Missing)
        | SOME _ => Invalid
end
