## Command line parsing: argv in, an `Options` value out. No I/O, no `quit()`,
## so every branch is a unit test rather than a subprocess.

type
  Mode* = enum
    ## Which figures to print; `all` prints lines, words and bytes.
    all, lines, words, bytes

  Status* = enum
    ## How parsing ended, which decides the exit code in the entry point.
    ok, helpShown, versionShown, usageError

  Options* = object
    ## A parsed command line.
    mode*: Mode ## The chosen mode; defaults to `all`.
    files*: seq[string] ## Files to read, in order; `-` means standard input.
    status*: Status ## Outcome of parsing.
    message*: string ## Error text for `usageError`, empty otherwise.

const
  version* = "0.1.0"

proc usage*(program: string): string =
  ## The help text. The caller passes the program name so it matches the binary
  ## that is actually being run.
  "usage: " & program & " [-l | -w | -c] [--] [FILE ...]\n" &
    "\n" &
    "Count lines, words and bytes in each FILE, or in standard input\n" &
    "when no FILE is given. With more than one FILE a total is printed.\n" &
    "\n" &
    "  -l, --lines     print the line count only\n" &
    "  -w, --words     print the word count only\n" &
    "  -c, --bytes     print the byte count only\n" &
    "  -h, --help      show this help and exit\n" &
    "  -V, --version   show the version and exit\n"

func modeFor(arg: string, mode: var Mode): bool =
  ## Sets `mode` and returns true when `arg` selects a figure.
  case arg
  of "-l", "--lines":
    mode = lines
    return true
  of "-w", "--words":
    mode = words
    return true
  of "-c", "--bytes":
    mode = bytes
    return true
  else:
    return false

func parseOptions*(args: seq[string]): Options =
  ## Parses `args` without the program name.
  ##
  ## Hand-rolled instead of `std/parseopt` on purpose: parseopt reports `--` as
  ## an empty long option and keeps parsing the arguments after it, so `-- -l`
  ## would still be read as a flag. Twenty lines of explicit loop behave the same
  ## on Nim 1.6 and 2.x, and the tests pin down each branch.
  result = Options(mode: all, status: ok)
  var chosen = false
  var optionsEnded = false

  for arg in args:
    if optionsEnded or arg.len == 0 or arg == "-":
      result.files.add(arg)
      continue
    if arg == "--":
      optionsEnded = true
      continue
    if arg == "-h" or arg == "--help":
      result.status = helpShown
      return
    if arg == "-V" or arg == "--version":
      result.status = versionShown
      return
    var requested: Mode
    if modeFor(arg, requested):
      if chosen and result.mode != requested:
        result.status = usageError
        result.message = "choose one of -l, -w, -c: '" & arg &
          "' conflicts with an earlier mode"
        return
      chosen = true
      result.mode = requested
      continue
    if arg.len > 0 and arg[0] == '-':
      result.status = usageError
      result.message = "unknown option '" & arg & "'"
      return
    result.files.add(arg)
