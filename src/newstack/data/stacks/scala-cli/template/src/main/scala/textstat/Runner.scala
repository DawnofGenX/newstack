package textstat

/** Everything the runner needs from the outside world, so tests can fake it. */
trait Io:
  def readFile(path: String): Either[String, Array[Byte]]
  def readStdin(): Array[Byte]
  def out(line: String): Unit
  def err(line: String): Unit

object Runner:
  val program: String = "{{ npm_name }}"

  /** 0 on success (or help/version), 1 for an unreadable file, 2 for a usage error. */
  def run(args: List[String], io: Io): Int =
    val parsed = Options.parse(args)
    parsed.status match
      case Status.Help =>
        io.out(Options.usage(program))
        0
      case Status.Version =>
        io.out(Options.version)
        0
      case Status.UsageError(message) =>
        io.err(s"$program: $message")
        io.err(s"Try '$program --help' for more information.")
        2
      case Status.Ok =>
        val paths = if parsed.files.isEmpty then List("-") else parsed.files
        runOk(paths, parsed.figures, io)

  private def runOk(paths: List[String], figures: Figures, io: Io): Int =
    var failed = false
    val rows = paths.flatMap { path =>
      val data = if path == "-" then Right(io.readStdin()) else io.readFile(path)
      data match
        case Right(bytes) => Some((path, Counts.ofBytes(bytes)))
        case Left(message) =>
          failed = true
          io.err(s"error: $message")
          None
    }
    // `wc` prints a total whenever more than one operand is given, even if some
    // of them could not be read, so this counts operands, not readable rows.
    val total =
      if paths.length > 1 then Some("total" -> rows.map(_._2).foldLeft(Counts.empty)(_.add(_)))
      else None
    val all = rows.map(_._2) ++ total.map(_._2).toList
    val width = Counts.width(all, figures)
    rows.foreach { case (label, counts) =>
      io.out(Counts.formatRow(figures, counts, label, width))
    }
    total.foreach { case (label, counts) =>
      io.out(Counts.formatRow(figures, counts, label, width))
    }
    if failed then 1 else 0
