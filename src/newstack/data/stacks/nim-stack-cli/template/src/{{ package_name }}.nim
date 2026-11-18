## Entry point: owns argv, stdin, stdout and the exit code.

import std/[os, strutils]

import {{ package_name }}/[options, vm]

const programName = "{{ package_name }}"

proc readStdin(): seq[string] =
  ## Whitespace-separated words, so a piped program can be laid out freely.
  for line in stdin.lines:
    for word in line.splitWhitespace():
      result.add(word)

proc run(args: seq[string]): int =
  ## 0 success, 1 a bad program, 2 bad usage. Never calls `quit()`, so this is
  ## callable from a test.
  let options = parseOptions(args)
  case options.status
  of helpShown:
    stdout.write(usage(programName))
    return 0
  of versionShown:
    stdout.writeLine(version)
    return 0
  of usageError:
    stderr.writeLine("error: " & options.message)
    stderr.writeLine("")
    stderr.write(usage(programName))
    return 2
  of ok:
    discard

  let words = if options.words.len > 0: options.words else: readStdin()
  if words.len == 0:
    stderr.writeLine("error: no program given")
    stderr.writeLine("")
    stderr.write(usage(programName))
    return 2

  var machine = newVm()
  try:
    eval(machine, words)
  except VmError as error:
    stderr.writeLine("error: " & error.msg)
    stdout.writeLine($machine)
    return 1

  stdout.writeLine($machine)
  return 0

when isMainModule:
  quit(run(commandLineParams()))
