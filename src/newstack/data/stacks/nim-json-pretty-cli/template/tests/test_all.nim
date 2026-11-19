## Test suite.

import std/[json, os, osproc, strutils, unittest]

import {{ package_name }}/[jsonpretty, options]

const
  binary = "./{{ package_name }}"
  binarySource = "src/{{ package_name }}.nim"

proc ensureBinary() =
  if fileExists(binary):
    return
  let (output, code) = execCmdEx("nim c --path:src -o:" & binary & " " & binarySource)
  doAssert code == 0, "could not build " & binary & ":\n" & output

proc runBinary(args: string): (string, int) =
  execCmdEx(binary & " " & args)

ensureBinary()

suite "jsonpretty":
  test "sorts keys recursively":
    let rendered = prettyJson("""{"b":2,"a":{"d":4,"c":3}}""")
    check rendered == """{
  "a": {
    "c": 3,
    "d": 4
  },
  "b": 2
}"""

  test "compact mode":
    check prettyJson("""{"b":2,"a":1}""", compact = true) == """{"a":1,"b":2}"""

  test "no sort keeps order":
    let rendered = prettyJson("""{"b":2,"a":1}""", sortKeys = false, compact = true)
    check rendered == """{"b":2,"a":1}"""

  test "custom indent":
    let rendered = prettyJson("""{"a":1}""", indent = 4)
    check rendered == """{
    "a": 1
}"""

  test "invalid json raises":
    var raised = false
    try:
      discard prettyJson("{bad")
    except CatchableError:
      raised = true
    check raised

suite "options":
  test "defaults":
    let o = parseOptions(@[])
    check o.status == ok
    check o.indent == 2
    check o.sortKeys == true
    check o.mode == Mode.pretty
    check o.input == ""

  test "compact flag":
    check parseOptions(@["--compact"]).mode == Mode.compact

  test "no-sort flag":
    check parseOptions(@["--no-sort"]).sortKeys == false

  test "indent value":
    check parseOptions(@["--indent", "4"]).indent == 4

  test "indent equals form":
    check parseOptions(@["--indent=0"]).indent == 0

  test "negative indent is usage error":
    check parseOptions(@["--indent", "-1"]).status == usageError

  test "invalid indent":
    check parseOptions(@["--indent", "x"]).status == usageError

  test "missing indent value":
    check parseOptions(@["--indent"]).status == usageError

  test "unknown flag":
    check parseOptions(@["--bogus"]).status == usageError

  test "too many files":
    check parseOptions(@["a.json", "b.json"]).status == usageError

  test "help":
    check parseOptions(@["--help"]).status == helpShown

  test "version":
    check parseOptions(@["-V"]).status == versionShown

suite "command line":
  test "help exits 0":
    let (output, code) = runBinary("--help")
    check code == 0
    check output.startsWith("usage: {{ package_name }}")

  test "version exits 0":
    let (_, code) = runBinary("--version")
    check code == 0

  test "unknown flag exits 2":
    let (_, code) = runBinary("--bogus")
    check code == 2

  test "invalid json exits 1":
    let (output, code) = execCmdEx("printf '{bad' | " & binary)
    check code == 1
    check "error" in output

  test "pretty from stdin":
    let (output, code) = execCmdEx("printf '{\"b\":2,\"a\":1}' | " & binary)
    check code == 0
    check "a" in output

  test "compact flag":
    let (output, code) = execCmdEx("printf '{\"b\":2,\"a\":1}' | " & binary & " --compact")
    check code == 0
    check output.strip() == """{"a":1,"b":2}"""

  test "file input":
    let path = "tests/fixture.json"
    writeFile(path, """{"x":1}""")
    let (output, code) = runBinary(path)
    removeFile(path)
    check code == 0
    check "x" in output