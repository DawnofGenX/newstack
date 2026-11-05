(* Entry point: read HOST and PORT, then block. *)
structure Main = struct
  fun parseInt (raw : string) =
      let
        val n = String.size raw
        fun go i acc =
            if i >= n then SOME acc
            else if Char.isDigit (String.sub (raw, i))
            then go (i + 1) (acc * 10 + (ord (String.sub (raw, i)) - ord #"0"))
            else NONE
      in
        if n = 0 then NONE else go 0 0
      end

  fun run () =
      let
        val host = case OS.Process.getEnv "HOST" of SOME h => h | NONE => "127.0.0.1"
        val raw = case OS.Process.getEnv "PORT" of SOME p => p | NONE => "8080"
        val port =
            case parseInt raw of
                SOME p => if p >= 1 andalso p <= 65535 then p else ~1
              | NONE => ~1
      in
        if port < 0 then
          (TextIO.output (TextIO.stdErr,
                          "PORT must be a number between 1 and 65535, got " ^ raw ^ "\n");
           OS.Process.exit OS.Process.failure)
        else (Server.serve (host, port); ())
      end
end

val () = Main.run ()
