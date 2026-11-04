(* argv parsing with no side effects: clusters, long forms and "--". *)
structure Options = struct
  type t = { lines : bool, words : bool, bytes : bool, operands : string list }
  datatype outcome = Run of t | Help | Version | Usage of string

  val version = "0.1.0"

  val empty : t = { lines = false, words = false, bytes = false, operands = [] }

  fun usage program =
    "Usage: " ^ program ^ " [OPTION]... [FILE]...\n"
    ^ "Print newline, word, and byte counts for each FILE.\n"
    ^ "With no FILE, or when FILE is -, read standard input.\n\n"
    ^ "  -l, --lines   print the newline counts\n"
    ^ "  -w, --words   print the word counts\n"
    ^ "  -c, --bytes   print the byte counts\n"
    ^ "  -h, --help    display this help and exit\n"
    ^ "      --version  output version information and exit\n"

  fun hasPrefix (prefix, text) =
    let
      val p = String.size prefix
      val t = String.size text
    in
      t >= p andalso String.substring (text, 0, p) = prefix
    end

  fun setFlag (options, ch) =
    case ch of
        #"l" => SOME { lines = true, words = #words options, bytes = #bytes options,
                       operands = #operands options }
      | #"w" => SOME { lines = #lines options, words = true, bytes = #bytes options,
                       operands = #operands options }
      | #"c" => SOME { lines = #lines options, words = #words options, bytes = true,
                       operands = #operands options }
      | _ => NONE

  fun parse args =
    let
      fun cluster (options, text, index) =
        if index >= String.size text then SOME options
        else
          case setFlag (options, String.sub (text, index)) of
              NONE => NONE
            | SOME next => cluster (next, text, index + 1)

      fun addOperand (options, operand) =
        { lines = #lines options, words = #words options, bytes = #bytes options,
          operands = #operands options @ [operand] }

      fun go (options, onlyOperands, remaining) =
        case remaining of
            [] =>
              if #lines options orelse #words options orelse #bytes options
              then Run options
              else Run { lines = true, words = true, bytes = true,
                         operands = #operands options }
          | arg :: rest =>
              if onlyOperands orelse arg = "-" orelse not (hasPrefix ("-", arg)) then
                go (addOperand (options, arg), onlyOperands, rest)
              else if arg = "--" then
                go (options, true, rest)
              else if arg = "--help" orelse arg = "-h" then Help
              else if arg = "--version" then Version
              else if hasPrefix ("--", arg) then
                (case arg of
                     "--lines" =>
                       go ({ lines = true, words = #words options, bytes = #bytes options,
                             operands = #operands options }, onlyOperands, rest)
                   | "--words" =>
                       go ({ lines = #lines options, words = true, bytes = #bytes options,
                             operands = #operands options }, onlyOperands, rest)
                   | "--bytes" =>
                       go ({ lines = #lines options, words = #words options, bytes = true,
                             operands = #operands options }, onlyOperands, rest)
                   | _ => Usage ("unrecognized option: " ^ arg))
              else
                (case cluster (options, arg, 1) of
                     SOME next => go (next, onlyOperands, rest)
                   | NONE => Usage ("invalid option: " ^ arg))
    in
      go (empty, false, args)
    end
end
