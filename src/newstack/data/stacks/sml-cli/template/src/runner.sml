(* Report building over an io record, so the tests can fake the disk. *)
structure Runner = struct
  type io = { readFile : string -> Word8Vector.vector,
              readStdin : unit -> Word8Vector.vector }

  type result = { out : string, err : string, code : int }

  type reading = { label : string, counts : Counts.t }

  fun pad (width, text) =
    if String.size text >= width then text
    else String.implode (List.tabulate (width - String.size text, fn _ => #" ")) ^ text

  fun digits (n : int) = String.size (Int.toString n)

  fun figures (options : Options.t) =
    (if #lines options then 1 else 0)
    + (if #words options then 1 else 0)
    + (if #bytes options then 1 else 0)

  fun width (operands : int, figureCount : int, total : Counts.t, hasStream : bool) =
    if operands = 1 andalso figureCount = 1 then 0
    else if hasStream then 7
    else digits (#bytes total)

  fun row (options : Options.t, counts : Counts.t, width, label) =
    let
      val cells =
        (if #lines options then [Int.toString (#lines counts)] else [])
        @ (if #words options then [Int.toString (#words counts)] else [])
        @ (if #bytes options then [Int.toString (#bytes counts)] else [])
      val padded = map (fn cell => pad (width, cell)) cells
      val text = String.concatWith " " padded
    in
      if label = "" then text ^ "\n" else text ^ " " ^ label ^ "\n"
    end

  fun run { program : string, args : string list, io : io } : result =
    case Options.parse args of
        Options.Help => { out = Options.usage program, err = "", code = 0 }
      | Options.Version => { out = program ^ " " ^ Options.version ^ "\n", err = "", code = 0 }
      | Options.Usage reason =>
          { out = "", err = program ^ ": " ^ reason ^ "\n" ^ Options.usage program, code = 2 }
      | Options.Run options =>
          let
            val implicitInput = null (#operands options)
            val operands = if implicitInput then ["-"] else #operands options
            val hasStream = implicitInput orelse List.exists (fn operand => operand = "-") operands

            fun readOne operand =
              if operand = "-" then (#readStdin io) ()
              else (#readFile io) operand

            fun attempt (operand, (readings, errors)) =
              let
                val outcome =
                  (SOME (readOne operand)) handle _ => NONE
              in
                case outcome of
                    NONE => (readings, errors @ [program ^ ": " ^ operand
                                                 ^ ": No such file or directory\n"])
                  | SOME payload =>
                      let
                        val label = if implicitInput then "" else operand
                      in
                        (readings @ [{ label = label, counts = Counts.count payload }], errors)
                      end
              end

            val (readings, errors) = List.foldl attempt ([], []) operands
            val total = List.foldl (fn (r, acc) => Counts.add (#counts r, acc)) Counts.zero readings
            val width = width (length operands, figures options, total, hasStream)
            val rows = List.map (fn r => row (options, #counts r, width, #label r)) readings
            val totalRows =
              if length operands > 1 then [row (options, total, width, "total")] else []
            val code = if null errors then 0 else 1
          in
            { out = String.concat (rows @ totalRows),
              err = String.concat errors,
              code = code }
          end
end
