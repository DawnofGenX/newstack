## One suite for the whole project: the machine, the parser and the real
## binary's exit codes. Standard library only (`unittest` + `osproc`).

import std/[os, osproc, strutils, unittest]

import {{ package_name }}/[options, vm]

const
  binary = "./{{ package_name }}"
  binarySource = "src/{{ package_name }}.nim"

proc ensureBinary() =
  ## `nimble test` compiles first; this keeps a bare
  ## `nim c -r tests/test_all.nim` honest too.
  if fileExists(binary):
    return
  let (output, code) = execCmdEx("nim c --path:src -o:" & binary & " " & binarySource)
  doAssert code == 0, "could not build " & binary & ":\n" & output

proc runBinary(args: string): (string, int) =
  execCmdEx(binary & " " & args)

proc evaluate(program: string): string =
  var machine = newVm()
  eval(machine, program.splitWhitespace())
  $machine

ensureBinary()

suite "vm":
  test "an empty program leaves an empty stack":
    check evaluate("") == ""

  test "addition pops two and pushes one":
    check evaluate("2 3 +") == "5"

  test "order matters for subtraction, division and remainder":
    check evaluate("7 2 -") == "5"
    check evaluate("7 2 /") == "3"
    check evaluate("7 2 %") == "1"

  test "negative results are ordinary values":
    check evaluate("2 7 -") == "-5"

  test "dup doubles the top value":
    check evaluate("4 dup") == "4 4"

  test "swap exchanges the top two":
    check evaluate("1 2 swap") == "2 1"

  test "drop removes the top value":
    check evaluate("1 2 3 drop") == "1 2"

  test "depth counts what is already on the stack":
    check evaluate("1 2 depth") == "1 2 2"

  test "abs and neg are unary":
    check evaluate("-9 abs") == "9"
    check evaluate("9 neg") == "-9"

  test "min and max keep one of the pair":
    check evaluate("3 8 min") == "3"
    check evaluate("3 8 max") == "8"

  test "underflow names the word and the depth it found":
    var machine = newVm()
    machine.push(1)
    var message = ""
    try:
      machine.step("+")
    except VmError as error:
      message = error.msg
    check message == "stack underflow: '+' needs two values, have 1"
    check $machine == "1"

  test "division by zero is refused":
    var machine = newVm()
    var raised = false
    try:
      eval(machine, @["1", "0", "/"])
    except VmError:
      raised = true
    check raised
    check $machine == ""

  test "an unknown word is named back to the user":
    var machine = newVm()
    var message = ""
    try:
      eval(machine, @["frobnicate"])
    except VmError as error:
      message = error.msg
    check message == "not a number or command: 'frobnicate'"

suite "options":
  test "no arguments means read standard input":
    let options = parseOptions(@[])
    check options.status == ok
    check options.words.len == 0

  test "words keep their order":
    check parseOptions(@["1", "2", "+"]).words == @["1", "2", "+"]

  test "a negative number is a word, not an option":
    let options = parseOptions(@["-5", "abs"])
    check options.status == ok
    check options.words == @["-5", "abs"]

  test "--help wins over later words":
    check parseOptions(@["--help", "1"]).status == helpShown

  test "-h is the short help":
    check parseOptions(@["-h"]).status == helpShown

  test "--version is its own outcome":
    check parseOptions(@["-V"]).status == versionShown

  test "an unknown option is a usage error, not a word":
    let options = parseOptions(@["--bogus"])
    check options.status == usageError
    check "unknown option '--bogus'" in options.message

  test "a letter option is rejected too":
    check parseOptions(@["-x"]).status == usageError

  test "-- ends option parsing":
    let options = parseOptions(@["--", "--bogus"])
    check options.status == ok
    check options.words == @["--bogus"]

suite "command line":
  test "--help exits 0 and prints the usage line":
    let (output, code) = runBinary("--help")
    check code == 0
    check output.startsWith("usage: {{ package_name }}")

  test "a program prints its stack and exits 0":
    let (output, code) = runBinary("2 3 +")
    check code == 0
    check output.strip() == "5"

  test "an unknown word exits 1 and keeps the partial stack":
    ## execCmdEx merges stdout and stderr, so the last line is the stack while
    ## the error line comes first.
    let (output, code) = runBinary("1 2 frobnicate")
    check code == 1
    check "not a number or command" in output
    check output.strip().splitLines()[^1] == "1 2"

  test "an unknown option exits 2":
    let (_, code) = runBinary("--nope")
    check code == 2

  test "no program at all exits 2":
    let (_, code) = runBinary("")
    check code == 2

  test "standard input is read when no word is given":
    let (output, code) = execCmdEx("printf '1 2 3 +\\n' | " & binary)
    check code == 0
    check output.strip() == "1 5"
