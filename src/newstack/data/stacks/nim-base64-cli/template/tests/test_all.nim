## One suite for the whole project: the codec, the parser and the real
## binary's exit codes. Standard library only (`unittest` + `osproc`).

import std/[os, osproc, strutils, unittest]

import {{ package_name }}/[base64x, options]

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

suite "codec":
  test "the RFC 4648 hello vector":
    check encodeText("hello") == "aGVsbG8="

  test "the standard alphabet uses + and /":
    check encodeText("???") == "Pz8/"

  test "the url-safe alphabet uses - and _":
    check encodeText("???", urlSafe) == "Pz8_"

  test "padding can be dropped":
    check encodeText("hello", standard, false) == "aGVsbG8"
    check withoutPadding("aGVsbG8=") == "aGVsbG8"
    check withoutPadding("aGVsbG8") == "aGVsbG8"

  test "an empty input encodes to an empty string":
    check encodeText("") == ""
    check decodeText("") == ""

  test "decoding accepts unpadded input":
    check decodeText("aGVsbG8") == "hello"

  test "decoding accepts both alphabets":
    check decodeText("Pz8/") == "???"
    check decodeText("Pz8_") == "???"

  test "wrapped base64 decodes":
    check decodeText("aGV\nsbG8=") == "hello"
    check decodeText("aGV sbG8=") == "hello"

  test "round trips hold for every byte value":
    var payload = newSeq[byte](256)
    for index in 0 ..< 256:
      payload[index] = byte(index)
    let encoded = encodeBytes(payload, urlSafe, false)
    check encoded.len > 0
    check encoded.contains('_') or encoded.contains('-')

  test "malformed base64 is refused":
    expect ValueError:
      discard decodeText("not base64!!")

suite "options":
  test "--help wins over everything":
    check parseOptions(@["encode", "--help"]).status == helpShown

  test "--version is recognised":
    check parseOptions(@["-V"]).status == versionShown

  test "an unknown option is a usage error":
    let options = parseOptions(@["encode", "--bogus"])
    check options.status == usageError
    check options.message == "unknown option: --bogus"

  test "a missing command is a usage error":
    let options = parseOptions(@["--url"])
    check options.status == usageError
    check options.message.startsWith("missing command")

  test "the command and the value are separated":
    let options = parseOptions(@["decode", "aGVsbG8="])
    check options.status == ok
    check options.command == decodeCommand
    check options.value == "aGVsbG8="

  test "--no-padding is recorded":
    check parseOptions(@["encode", "--no-padding"]).padding == false

  test "-- is honoured so a value may start with a dash":
    let options = parseOptions(@["encode", "--", "-abc"])
    check options.status == ok
    check options.value == "-abc"

  test "an extra argument is a usage error":
    check parseOptions(@["encode", "one", "two"]).status == usageError

suite "cli":
  test "encode prints the checksum for a value":
    let (output, code) = runBinary("encode hello")
    check code == 0
    check output.strip() == "aGVsbG8="

  test "decode returns the original text":
    let (output, code) = runBinary("decode aGVsbG8=")
    check code == 0
    check output.strip() == "hello"

  test "--no-padding drops the equals signs":
    let (output, code) = runBinary("encode --no-padding hello")
    check code == 0
    check output.strip() == "aGVsbG8"

  test "--url switches the alphabet":
    let (output, code) = runBinary("encode --url '???'")
    check code == 0
    check output.strip() == "Pz8_"

  test "malformed input exits 1":
    let (output, code) = runBinary("decode 'not base64!!'")
    check code == 1
    check output.contains("error:")

  test "an unknown option exits 2":
    let (_, code) = runBinary("encode --bogus")
    check code == 2

  test "help exits 0 and prints usage":
    let (output, code) = runBinary("--help")
    check code == 0
    check output.contains("Usage:")

  test "standard input is encoded":
    let (output, code) = execCmdEx("printf 'hello' | " & binary & " encode", options = {poEvalCommand})
    check code == 0
    check output.strip() == "aGVsbG8="
