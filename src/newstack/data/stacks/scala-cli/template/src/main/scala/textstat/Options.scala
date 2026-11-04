package textstat

/** How a command line was resolved. */
enum Status:
  case Ok
  case Help
  case Version
  case UsageError(message: String)

/** A parsed command line: what to print, what to read, and whether to run at all. */
final case class Parsed(figures: Figures, files: List[String], status: Status)

object Options:
  val version: String = "0.1.0"

  def usage(program: String): String =
    s"""Usage: $program [-l] [-w] [-c] [FILE...]
       |
       |Print newline, word and byte counts for each FILE, and a total line if
       |more than one FILE is given. With no FILE, or when FILE is -, read
       |standard input. With no flag, all three figures are printed.
       |
       |  -l, --lines   print the newline count
       |  -w, --words   print the word count
       |  -c, --bytes   print the byte count
       |  -h, --help    print this help and exit
       |  -V, --version print the version and exit
       |""".stripMargin

  private def appendFlag(figures: Figures, flag: Char): Option[Figures] =
    flag match
      case 'l' => Some(figures.copy(lines = true))
      case 'w' => Some(figures.copy(words = true))
      case 'c' => Some(figures.copy(bytes = true))
      case _   => None

  /** Fold the short flags of one argument (`-lw`, or `-w` alone). */
  private def shortFlags(figures: Figures, arg: String): Either[String, Figures] =
    arg.drop(1).foldLeft[Either[String, Figures]](Right(figures)) { (acc, flag) =>
      acc.flatMap(current => appendFlag(current, flag).toRight(s"unknown option: -$flag"))
    }

  private def longFlag(figures: Figures, arg: String): Either[String, Figures] =
    arg match
      case "--lines"   => Right(figures.copy(lines = true))
      case "--words"   => Right(figures.copy(words = true))
      case "--bytes"   => Right(figures.copy(bytes = true))
      case other       => Left(s"unknown option: $other")

  def parse(args: List[String]): Parsed =
    def loop(
        remaining: List[String],
        figures: Figures,
        files: List[String],
        onlyFiles: Boolean
    ): Parsed =
      remaining match
        case Nil =>
          val chosen = if figures == Figures.none then Figures.all else figures
          Parsed(chosen, files.reverse, Status.Ok)
        case arg :: rest if onlyFiles =>
          loop(rest, figures, arg :: files, onlyFiles = true)
        case ("--" :: rest) =>
          loop(rest, figures, files, onlyFiles = true)
        case ("-h" :: _) | ("--help" :: _) =>
          Parsed(figures, Nil, Status.Help)
        case ("-V" :: _) | ("--version" :: _) =>
          Parsed(figures, Nil, Status.Version)
        case arg :: rest if arg.startsWith("--") =>
          longFlag(figures, arg) match
            case Right(updated) => loop(rest, updated, files, onlyFiles = false)
            case Left(message)  => Parsed(figures, files.reverse, Status.UsageError(message))
        case arg :: rest if arg.startsWith("-") && arg.length > 1 =>
          shortFlags(figures, arg) match
            case Right(updated) => loop(rest, updated, files, onlyFiles = false)
            case Left(message)  => Parsed(figures, files.reverse, Status.UsageError(message))
        case arg :: rest =>
          loop(rest, figures, arg :: files, onlyFiles = false)

    loop(args, Figures.none, Nil, onlyFiles = false)
