package textstat

import java.nio.file.{Files, Paths}

/** The only place that touches the real process: argv, stdin/stdout and the exit code. */
object Main:
  private object SystemIo extends Io:
    def readFile(path: String): Either[String, Array[Byte]] =
      try Right(Files.readAllBytes(Paths.get(path)))
      catch
        case _: java.nio.file.NoSuchFileException => Left(s"cannot open '$path'")
        case _: java.io.IOException              => Left(s"cannot open '$path'")

    def readStdin(): Array[Byte] =
      System.in.readAllBytes()

    def out(line: String): Unit =
      System.out.println(line)

    def err(line: String): Unit =
      System.err.println(line)

  def main(args: Array[String]): Unit =
    val code = Runner.run(args.toList, SystemIo)
    System.out.flush()
    System.err.flush()
    sys.exit(code)
