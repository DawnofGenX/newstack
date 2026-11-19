## Entry point: owns argv, stdin, stdout and the exit code.

import std/os

import {{ package_name }}/[base64x, options]

const programName = "{{ package_name }}"

proc readStdin(): string =
  ## Reads standard input as text. A single trailing newline is dropped, the
  ## way `wc` and `sha256sum` treat piped text.
  var first = true
  for line in stdin.lines:
    if not first:
      result.add('\n')
    result.add(line)
    first = false

proc run(args: seq[string]): int =
  ## 0 success, 1 malformed base64, 2 bad usage. Never calls `quit()` so the
  ## tests can drive it directly.
  let options = parseOptions(args)
  case options.status
  of helpShown:
    stdout.write(usage(programName))
    return 0
  of versionShown:
    stdout.writeLine(Version)
    return 0
  of usageError:
    stderr.writeLine("error: " & options.message)
    stderr.writeLine("")
    stderr.write(usage(programName))
    return 2
  of ok:
    discard

  let flavour = if options.flavour == urlFlavour: urlSafe else: standard
  let payload =
    if options.value.len > 0: options.value
    else: readStdin()

  case options.command
  of encodeCommand:
    if options.value.len == 0:
      stdout.write(encodeText(payload, flavour, options.padding))
      stdout.writeLine("")
      return 0
    stdout.writeLine(encodeText(payload, flavour, options.padding))
    return 0
  of decodeCommand:
    try:
      let decoded = decodeText(payload, flavour)
      stdout.writeLine(decoded)
      return 0
    except ValueError as error:
      stderr.writeLine("error: " & error.msg)
      return 1

when isMainModule:
  quit(run(commandLineParams()))
