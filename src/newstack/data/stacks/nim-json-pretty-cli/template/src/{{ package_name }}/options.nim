## Command line parsing for the JSON pretty printer.

import std/strutils

type
  Mode* = enum
    pretty, compact

  Status* = enum
    ok, helpShown, versionShown, usageError

  Options* = object
    mode*: Mode
    indent*: int
    sortKeys*: bool
    input*: string
    status*: Status
    message*: string

const
  version* = "0.1.0"

proc usage*(program: string): string =
  "usage: " & program & " [--indent N] [--compact] [--no-sort] [FILE]\n" &
  "\n" &
  "Pretty print JSON, sorting object keys by default.\n" &
  "\n" &
  "  --indent N    spaces per level (default 2)\n" &
  "  --compact     emit compact JSON instead of pretty\n" &
  "  --no-sort     keep original key order\n" &
  "  -h, --help    show this help and exit\n" &
  "  -V, --version show the version and exit\n" &
  "\n" &
  "Reads from FILE or stdin when FILE is omitted or '-'.\n"

func parseOptions*(args: seq[string]): Options =
  result = Options(mode: pretty, indent: 2, sortKeys: true, status: ok)
  var i = 0
  while i < args.len:
    let arg = args[i]
    if arg == "-h" or arg == "--help":
      result.status = helpShown
      return
    if arg == "-V" or arg == "--version":
      result.status = versionShown
      return
    if arg == "--compact":
      result.mode = compact
      i += 1
      continue
    if arg == "--no-sort":
      result.sortKeys = false
      i += 1
      continue
    if arg == "--indent":
      if i + 1 >= args.len:
        result.status = usageError
        result.message = "missing value for --indent"
        return
      try:
        result.indent = parseInt(args[i+1])
      except ValueError:
        result.status = usageError
        result.message = "invalid indent: " & args[i+1]
        return
      if result.indent < 0:
        result.status = usageError
        result.message = "indent must be >= 0"
        return
      i += 2
      continue
    if arg.startsWith("--indent="):
      let v = arg["--indent=".len .. ^1]
      try:
        result.indent = parseInt(v)
      except ValueError:
        result.status = usageError
        result.message = "invalid indent: " & v
        return
      if result.indent < 0:
        result.status = usageError
        result.message = "indent must be >= 0"
        return
      i += 1
      continue
    if arg.len > 0 and arg[0] == '-':
      result.status = usageError
      result.message = "unknown option '" & arg & "'"
      return
    if result.input.len > 0:
      result.status = usageError
      result.message = "too many input files"
      return
    result.input = arg
    i += 1