## Entry point.

import std/[os, strutils]

import {{ package_name }}/[jsonpretty, options]

const programName = "{{ package_name }}"

proc readInput(path: string): string =
  if path == "" or path == "-":
    return stdin.readAll()
  return readFile(path)

proc run(args: seq[string]): int =
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

  var text: string
  try:
    text = readInput(options.input)
  except CatchableError:
    stderr.writeLine("error: cannot read input")
    return 1

  try:
    let rendered = prettyJson(text, options.indent, options.sortKeys,
                        options.mode == compact)
    stdout.writeLine(rendered)
    return 0
  except CatchableError as e:
    stderr.writeLine("error: " & e.msg)
    return 1

when isMainModule:
  quit(run(commandLineParams()))