## Arguments in, an `Options` value out. No I/O and no `quit()`, so the entry
## point stays a thin shell around this and every branch is a unit test.

type
  Status* = enum
    ## How parsing ended; the entry point turns this into an exit code.
    ok, helpShown, versionShown, usageError

  Options* = object
    words*: seq[string] ## Tokens to evaluate, in order.
    status*: Status
    message*: string ## Filled in for `usageError` only.

const
  version* = "0.1.0"

proc usage*(program: string): string =
  ## The help text, with the program name the user actually typed.
  "usage: " & program & " [--] [WORD ...]\n" &
    "\n" &
    "Evaluate a stack-language program: push integers, then combine them.\n" &
    "With no WORD the program is read from standard input.\n" &
    "\n" &
    "  arithmetic   + - * / %\n" &
    "  stack        dup swap drop depth\n" &
    "  unary        abs neg\n" &
    "  binary       min max\n" &
    "\n" &
    "  -h, --help      show this help and exit\n" &
    "  -V, --version   show the version and exit\n" &
    "  --              treat every later WORD as a word, not an option\n" &
    "\n" &
    "Negative numbers are words, not options: -5 pushes minus five.\n"

func looksLikeOption(arg: string): bool =
  ## A dash followed by a digit is a negative number (`-5`); anything else that
  ## starts with a dash has to be an option, known or not.
  if arg.len < 2 or arg[0] != '-':
    return false
  not (arg[1] in {'0'..'9'})

func parseOptions*(args: seq[string]): Options =
  ## Parses `args` without the program name.
  ##
  ## Hand-rolled instead of `std/parseopt`: parseopt reports `--` as an empty
  ## long option and keeps parsing what follows it, so `-- --bogus` would still
  ## be read as a flag.
  result = Options(words: @[], status: ok)
  var optionsEnded = false

  for arg in args:
    if optionsEnded:
      result.words.add(arg)
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
    if looksLikeOption(arg):
      result.status = usageError
      result.message = "unknown option '" & arg & "'"
      return
    result.words.add(arg)
