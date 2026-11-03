## One suite for the whole project: the counting module, the parser and the real
## binary's exit codes. Standard library only (`unittest` + `osproc`).

import std/[os, osproc, strutils, unittest]

import {{ package_name }}/[counting, options]

const
  binary = "./{{ package_name }}"
  binarySource = "src/{{ package_name }}.nim"

proc ensureBinary() =
  ## `nimble test` compiles the binary first; this keeps a bare
  ## `nim c -r tests/test_all.nim` honest too.
  if fileExists(binary):
    return
  let (output, code) = execCmdEx("nim c --path:src -o:" & binary & " " & binarySource)
  doAssert code == 0, "could not build " & binary & ":\n" & output

proc runBinary(args: string): (string, int) =
  ## Runs the built binary with a shell command line and returns (output, code).
  execCmdEx(binary & " " & args)

ensureBinary()

suite "counting":
  test "empty input has no lines, words or bytes":
    check count("") == Counts(lines: 0, words: 0, bytes: 0)

  test "a trailing newline counts as a line":
    check count("hello\n") == Counts(lines: 1, words: 1, bytes: 6)

  test "input without a trailing newline has no lines":
    check count("hello") == Counts(lines: 0, words: 1, bytes: 5)

  test "extra spaces separate words without adding empty ones":
    check count("  a   b  ") == Counts(lines: 0, words: 2, bytes: 9)

  test "tabs and carriage returns are whitespace, newline ends a line":
    check count("\ta\r\nb\n") == Counts(lines: 2, words: 2, bytes: 6)

  test "several lines are counted once each":
    check count("one two\nthree\n") == Counts(lines: 2, words: 3, bytes: 14)

  test "totals add field by field":
    check count("a b\n") + count("c\n") == Counts(lines: 2, words: 3, bytes: 6)

suite "options":
  test "no arguments means all figures and stdin":
    let options = parseOptions(@[])
    check options.status == ok
    check options.mode == Mode.all
    check options.files.len == 0

  test "-l selects lines and keeps the file":
    let options = parseOptions(@["-l", "a.txt"])
    check options.status == ok
    check options.mode == Mode.lines
    check options.files == @["a.txt"]

  test "--words is the long form of -w":
    check parseOptions(@["--words"]).mode == Mode.words

  test "repeating the same mode is allowed":
    check parseOptions(@["-l", "--lines"]).mode == Mode.lines
    check parseOptions(@["-c", "--bytes"]).mode == Mode.bytes

  test "conflicting modes are a usage error":
    let options = parseOptions(@["-l", "-c"])
    check options.status == usageError
    check "conflicts" in options.message

  test "--help stops parsing":
    check parseOptions(@["--help", "-l"]).status == helpShown

  test "-h is the short form of --help":
    check parseOptions(@["-h"]).status == helpShown

  test "--version is a separate outcome":
    check parseOptions(@["-V"]).status == versionShown

  test "an unknown flag is a usage error":
    let options = parseOptions(@["--bogus"])
    check options.status == usageError
    check "unknown option '--bogus'" in options.message

  test "-- ends option parsing":
    let options = parseOptions(@["--", "-l"])
    check options.status == ok
    check options.mode == Mode.all
    check options.files == @["-l"]

  test "a bare - is standard input, not a flag":
    let options = parseOptions(@["-"])
    check options.status == ok
    check options.files == @["-"]

suite "command line":
  test "--help exits 0 and prints usage":
    let (output, code) = runBinary("--help")
    check code == 0
    check output.startsWith("usage: {{ package_name }}")

  test "an unknown flag exits 2":
    let (_, code) = runBinary("--bogus")
    check code == 2

  test "a missing file exits 1":
    let (output, code) = runBinary("does-not-exist.txt")
    check code == 1
    check "cannot open" in output

  test "a real file is counted":
    let path = "tests/fixture.txt"
    writeFile(path, "hello world\n")
    let (output, code) = runBinary(path)
    removeFile(path)
    check code == 0
    # "hello world\n": one line, two words, twelve bytes, then the path.
    check output.strip().splitWhitespace() == @["1", "2", "12", "tests/fixture.txt"]

  test "standard input can be counted when no file is given":
    let (output, code) = execCmdEx("printf 'a b\\n' | " & binary)
    check code == 0
    check output.strip().splitWhitespace() == @["1", "2", "4"]
