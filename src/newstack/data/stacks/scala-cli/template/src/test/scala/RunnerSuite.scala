package textstat

import scala.collection.mutable

class RunnerSuite extends munit.FunSuite:
  /** A fake environment: fixed files, fixed stdin, captured output. */
  final class FakeIo(files: Map[String, String], stdin: String = "") extends Io:
    val outLines: mutable.Buffer[String] = mutable.ArrayBuffer.empty
    val errLines: mutable.Buffer[String] = mutable.ArrayBuffer.empty

    def readFile(path: String): Either[String, Array[Byte]] =
      files.get(path).map(_.getBytes("UTF-8")).toRight(s"cannot open '$path'")

    def readStdin(): Array[Byte] = stdin.getBytes("UTF-8")
    def out(line: String): Unit = outLines += line
    def err(line: String): Unit = errLines += line

  private val files = Map(
    "a.txt" -> "alpha beta\ngamma\n",
    "b.txt" -> "one\n"
  )

  test("a readable file prints one row and exits 0") {
    val io = FakeIo(files)
    assertEquals(Runner.run(List("a.txt"), io), 0)
    assertEquals(io.outLines.toList, List(" 2  3 17 a.txt"))
    assertEquals(io.errLines.toList, Nil)
  }

  test("columns are right-aligned to the widest figure") {
    val io = FakeIo(Map("big.txt" -> "x " * 12))
    assertEquals(Runner.run(List("big.txt"), io), 0)
    assertEquals(io.outLines.toList, List(" 0 12 24 big.txt"))
  }

  test("more than one file adds a total row") {
    val io = FakeIo(files)
    assertEquals(Runner.run(List("a.txt", "b.txt"), io), 0)
    assertEquals(io.outLines.toList, List(" 2  3 17 a.txt", " 1  1  4 b.txt", " 3  4 21 total"))
  }

  test("an unreadable file is reported, the others are still counted, exit 1") {
    val io = FakeIo(files)
    assertEquals(Runner.run(List("missing.txt", "a.txt"), io), 1)
    assertEquals(io.outLines.toList, List(" 2  3 17 a.txt", " 2  3 17 total"))
    assertEquals(io.errLines.toList, List("error: cannot open 'missing.txt'"))
  }

  test("no file argument reads standard input") {
    val io = FakeIo(Map.empty, stdin = "hi there\n")
    assertEquals(Runner.run(Nil, io), 0)
    assertEquals(io.outLines.toList, List("1 2 9 -"))
  }

  test("a lone dash is standard input too") {
    val io = FakeIo(Map.empty, stdin = "hi there\n")
    assertEquals(Runner.run(List("-"), io), 0)
    assertEquals(io.outLines.toList, List("1 2 9 -"))
  }

  test("a single figure prints only that column") {
    val io = FakeIo(files)
    assertEquals(Runner.run(List("-w", "a.txt"), io), 0)
    assertEquals(io.outLines.toList, List("3 a.txt"))
  }

  test("help exits 0 and prints usage on stdout") {
    val io = FakeIo(Map.empty)
    assertEquals(Runner.run(List("--help"), io), 0)
    assertEquals(io.errLines.toList, Nil)
    assert(io.outLines.mkString("\n").contains("Usage:"), io.outLines.mkString("\n"))
  }

  test("version exits 0") {
    val io = FakeIo(Map.empty)
    assertEquals(Runner.run(List("--version"), io), 0)
    assertEquals(io.outLines.toList, List(Options.version))
  }

  test("a usage error exits 2 and explains itself on stderr") {
    val io = FakeIo(Map.empty)
    assertEquals(Runner.run(List("--bogus"), io), 2)
    assertEquals(io.outLines.toList, Nil)
    assert(io.errLines.head.contains("--bogus"), io.errLines.head)
  }

  test("help wins over a usage error that comes later") {
    val io = FakeIo(Map.empty)
    assertEquals(Runner.run(List("--help", "--bogus"), io), 0)
  }
