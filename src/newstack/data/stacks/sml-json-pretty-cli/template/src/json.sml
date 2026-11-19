
structure Json = struct
  datatype json = JNull
                | JBool of bool
                | JNum of string
                | JStr of string
                | JArr of json list
                | JObj of (string * json) list

  exception Parse of string

  fun isSpace c = Char.isSpace c

  fun skipws [] = []
    | skipws (c :: cs) = if isSpace c then skipws cs else c :: cs

  fun parseString (#"\"" :: rest) =
        let
          fun loop acc [] = raise Parse "unterminated string"
            | loop acc (#"\"" :: r) = (String.implode (List.rev acc), r)
            | loop acc (#"\\" :: c :: r) = loop (c :: #"\\" :: acc) r
            | loop acc (c :: r) = loop (c :: acc) r
        in
          loop [] rest
        end
    | parseString _ = raise Parse "expected string"

  fun parseLiteral (name, value, cs) =
    let
      val n = String.size name
      val prefix = List.take (cs, n) handle _ => []
    in
      if String.implode prefix = name then
        (value, List.drop (cs, n))
      else
        raise Parse ("expected " ^ name)
    end

  fun parseNumber (cs) =
    let
      fun isNumChar c = Char.isDigit c orelse c = #"-" orelse c = #"+" orelse c = #"." orelse c = #"e" orelse c = #"E"
      fun loop acc [] = (String.implode (List.rev acc), [])
        | loop acc (c :: rest) = if isNumChar c then loop (c :: acc) rest else (String.implode (List.rev acc), c :: rest)
      val (num, rest) = loop [] cs
    in
      if num = "" then raise Parse "expected number" else (JNum num, rest)
    end

  fun parseValue cs =
    case skipws cs of
        [] => raise Parse "unexpected end of input"
      | #"{" :: rest => parseObject rest
      | #"[" :: rest => parseArray rest
      | #"\"" :: _ => let val (s, r) = parseString cs in (JStr s, r) end
      | #"t" :: _ => let val (v, r) = parseLiteral ("true", JBool true, cs) in (v, r) end
      | #"f" :: _ => let val (v, r) = parseLiteral ("false", JBool false, cs) in (v, r) end
      | #"n" :: _ => let val (v, r) = parseLiteral ("null", JNull, cs) in (v, r) end
      | c :: _ => if Char.isDigit c orelse c = #"-" orelse c = #"+" then parseNumber cs
                  else raise Parse "unexpected character"

  and parseArray cs =
    case skipws cs of
        #"]" :: rest => (JArr [], rest)
      | _ => parseArrayItems (skipws cs) []

  and parseArrayItems cs acc =
    let
      val (v, rest) = parseValue cs
      val rest' = skipws rest
    in
      case rest' of
          #"," :: r => parseArrayItems (skipws r) (v :: acc)
        | #"]" :: r => (JArr (List.rev (v :: acc)), r)
        | _ => raise Parse "expected , or ] in array"
    end

  and parseObject cs =
    case skipws cs of
        #"}" :: rest => (JObj [], rest)
      | _ => parseObjectMembers (skipws cs) []

  and parseObjectMembers cs acc =
    let
      val (key, rest) = parseString (skipws cs)
      val rest1 = skipws rest
      val rest2 = case rest1 of #":" :: r => r | _ => raise Parse "expected :"
      val (value, rest3) = parseValue rest2
      val rest4 = skipws rest3
    in
      case rest4 of
          #"," :: r => parseObjectMembers (skipws r) ((key, value) :: acc)
        | #"}" :: r => (JObj (List.rev ((key, value) :: acc)), r)
        | _ => raise Parse "expected , or } in object"
    end

  fun parse (s : string) : json =
    let
      val chars = String.explode s
      val (value, rest) = parseValue chars
      val rest' = skipws rest
    in
      if null rest' then value else raise Parse "trailing garbage"
    end

  fun sortPairs [] = []
    | sortPairs (x :: xs) =
        let
          fun insert (y, []) = [y]
            | insert (y, z :: zs) =
                if String.compare (#1 y, #1 z) = LESS then y :: z :: zs
                else z :: insert (y, zs)
        in
          insert (x, sortPairs xs)
        end

  fun spaces 0 = ""
    | spaces n = " " ^ spaces (n - 1)

  fun indent n = String.implode (List.tabulate (n * 2, fn _ => #" "))

  fun prettyAt level (JNull) = "null"
    | prettyAt level (JBool true) = "true"
    | prettyAt level (JBool false) = "false"
    | prettyAt level (JNum s) = s
    | prettyAt level (JStr s) = "\"" ^ s ^ "\""
    | prettyAt level (JArr []) = "[]"
    | prettyAt level (JArr items) =
        let
          val inner = String.concatWith ",\n" (map (fn j => indent (level + 1) ^ prettyAt (level + 1) j) items)
        in
          "[\n" ^ inner ^ "\n" ^ indent level ^ "]"
        end
    | prettyAt level (JObj []) = "{}"
    | prettyAt level (JObj pairs) =
        let
          val sorted = sortPairs pairs
          val inner = String.concatWith ",\n" (map (fn (k, v) => indent (level + 1) ^ "\"" ^ k ^ "\": " ^ prettyAt (level + 1) v) sorted)
        in
          "{\n" ^ inner ^ "\n" ^ indent level ^ "}"
        end

  fun pretty (j : json) : string = prettyAt 0 j
end
