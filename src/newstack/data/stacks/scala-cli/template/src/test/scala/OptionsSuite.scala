package textstat

class OptionsSuite extends munit.FunSuite:
  test("no arguments means every figure and standard input") {
    val parsed = Options.parse(Nil)
    assertEquals(parsed.figures, Figures.all)
    assertEquals(parsed.files, Nil)
    assertEquals(parsed.status, Status.Ok)
  }

  test("short flags combine in any order") {
    assertEquals(Options.parse(List("-lw")).figures, Figures(lines = true, words = true, bytes = false))
    assertEquals(Options.parse(List("-wl")).figures, Figures(lines = true, words = true, bytes = false))
    assertEquals(Options.parse(List("-c", "-l")).figures, Figures(lines = true, words = false, bytes = true))
  }

  test("long flags are accepted too") {
    assertEquals(Options.parse(List("--words")).figures, Figures(lines = false, words = true, bytes = false))
  }

  test("flags before and after files both apply") {
    val parsed = Options.parse(List("-l", "a.txt", "-w", "b.txt"))
    assertEquals(parsed.figures, Figures(lines = true, words = true, bytes = false))
    assertEquals(parsed.files, List("a.txt", "b.txt"))
  }

  test("double dash ends flag parsing") {
    val parsed = Options.parse(List("--", "-w", "file"))
    assertEquals(parsed.figures, Figures.all)
    assertEquals(parsed.files, List("-w", "file"))
  }

  test("a lone dash is standard input, not a flag") {
    assertEquals(Options.parse(List("-")).files, List("-"))
  }

  test("help and version short-circuit") {
    assertEquals(Options.parse(List("-h")).status, Status.Help)
    assertEquals(Options.parse(List("--help")).status, Status.Help)
    assertEquals(Options.parse(List("-V")).status, Status.Version)
    assertEquals(Options.parse(List("--version")).status, Status.Version)
  }

  test("an unknown short flag is a usage error") {
    Options.parse(List("-x")) match
      case Parsed(_, _, Status.UsageError(message)) => assert(message.contains("-x"), message)
      case other                                    => fail(s"expected a usage error, got $other")
  }

  test("an unknown long flag is a usage error") {
    Options.parse(List("--bogus")) match
      case Parsed(_, _, Status.UsageError(message)) => assert(message.contains("--bogus"), message)
      case other                                    => fail(s"expected a usage error, got $other")
  }

  test("one bad flag in a cluster is still reported") {
    Options.parse(List("-lx")) match
      case Parsed(_, _, Status.UsageError(message)) => assert(message.contains("-x"), message)
      case other                                    => fail(s"expected a usage error, got $other")
  }
