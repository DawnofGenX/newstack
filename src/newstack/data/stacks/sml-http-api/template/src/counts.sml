(* The counting core. Everything is bytes: an SML string is a byte sequence, so
   the UTF-8 byte count is just its size. *)
structure Counts = struct
  type counts = {lines : int, words : int, bytes : int}

  (* wc's notion of a separator: exactly these six, nothing more. *)
  fun isSep b =
      b = 0w32 orelse b = 0w9 orelse b = 0w10 orelse b = 0w13
      orelse b = 0w11 orelse b = 0w12

  fun count (text : string) : counts =
      let
        val bytes = Byte.stringToBytes text
        val n = Word8Vector.length bytes
        fun loop i (lines, words, inWord) =
            if i >= n then (lines, words)
            else
              let
                val b = Word8Vector.sub (bytes, i)
                val lines' = if b = 0w10 then lines + 1 else lines
              in
                if isSep b then loop (i + 1) (lines', words, false)
                else if inWord then loop (i + 1) (lines', words, true)
                else loop (i + 1) (lines', words + 1, true)
              end
        val (lines, words) = loop 0 (0, 0, false)
      in
        {lines = lines, words = words, bytes = n}
      end
end
