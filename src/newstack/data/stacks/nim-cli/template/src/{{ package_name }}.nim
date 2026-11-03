## Entry point: owns argv, stdout/stderr and the exit code. All counting and
## parsing lives in the package modules so it can be tested without spawning a
## process.

import std/[os, strutils]

import {{ package_name }}/[counting, options]

## The binary nimble installs is the package name, so the usage line matches
## what the user actually typed.
const programName = "{{ package_name }}"

proc printCounts(counts: Counts, mode: Mode, label: string) =
  ## Prints the requested figures right-aligned like `wc`, then the label.
  var line = ""
  if mode == Mode.all or mode == Mode.lines:
    line.add(align($counts.lines, 8))
  if mode == Mode.all or mode == Mode.words:
    line.add(align($counts.words, 8))
  if mode == Mode.all or mode == Mode.bytes:
    line.add(align($counts.bytes, 8))
  if label.len > 0:
    line.add(" ")
    line.add(label)
  stdout.writeLine(line)

proc readStdin(): string =
  ## Drains standard input, so `-` and "no FILE" count piped text.
  stdin.readAll()

proc run(args: seq[string]): int =
  ## Turns argv into output and an exit code: 0 success, 1 unreadable file,
  ## 2 bad usage. Nothing here calls `quit()`, so `run` stays testable.
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

  if options.files.len == 0:
    printCounts(count(readStdin()), options.mode, "")
    return 0

  var total: Counts
  var failed = false
  for path in options.files:
    var counts: Counts
    if path == "-":
      counts = count(readStdin())
      printCounts(counts, options.mode, "")
    else:
      try:
        counts = count(readFile(path))
      except CatchableError:
        stderr.writeLine("error: cannot open '" & path & "'")
        failed = true
        continue
      printCounts(counts, options.mode, path)
    total = total + counts

  if options.files.len > 1:
    printCounts(total, options.mode, "total")
  if failed:
    return 1
  return 0

when isMainModule:
  quit(run(commandLineParams()))
