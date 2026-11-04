(* Counting that matches wc(1): lines are 0x0A bytes, words are maximal runs of
   non-whitespace bytes, bytes is the payload length. *)
structure Counts = struct
  type t = { lines : int, words : int, bytes : int }

  fun isSpace (w : Word8.word) =
    w = 0wx20 orelse w = 0wx09 orelse w = 0wx0A
    orelse w = 0wx0D orelse w = 0wx0B orelse w = 0wx0C

  fun count (payload : Word8Vector.vector) : t =
    let
      val n = Word8Vector.length payload
      fun loop (i, lines, words, inWord) =
        if i >= n then { lines = lines, words = words, bytes = n }
        else
          let
            val w = Word8Vector.sub (payload, i)
            val lines = if w = 0wx0A then lines + 1 else lines
          in
            if isSpace w then loop (i + 1, lines, words, false)
            else if inWord then loop (i + 1, lines, words, true)
            else loop (i + 1, lines, words + 1, true)
          end
    in
      loop (0, 0, 0, false)
    end

  val zero : t = { lines = 0, words = 0, bytes = 0 }

  fun add (a : t, b : t) : t =
    { lines = #lines a + #lines b,
      words = #words a + #words b,
      bytes = #bytes a + #bytes b }
end
