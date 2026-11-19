## A hand-written argument parser.
##
## `std/parseopt` is deliberately not used: it treats a bare `-` as a short
## option and mishandles `--`, and this tool has to accept base64 that starts
## with `-` when the caller passes it after `--`.

type
  Command* = enum
    encodeCommand, decodeCommand
  Status* = enum
    ok, helpShown, versionShown, usageError
  Options* = object
    status*: Status
    message*: string
    command*: Command
    flavour*: FlavourHint
    padding*: bool
    value*: string
  FlavourHint* = enum
    autoFlavour, standardFlavour, urlFlavour

const
  Version* = "0.1.0"

proc usage*(program: string): string =
  result = "Usage: " & program & " <encode|decode> [options] [VALUE]\n\n"
  result.add "Encodes VALUE (or standard input) as base64, or decodes it back.\n\n"
  result.add "Options:\n"
  result.add "  --url          use the URL-safe alphabet (-_ instead of +/)\n"
  result.add "  --no-padding   omit the trailing '=' characters when encoding\n"
  result.add "  -h, --help     show this help and exit\n"
  result.add "  -V, --version  print the version and exit\n\n"
  result.add "Exit codes:\n"
  result.add "  0  success (or --help/--version)\n"
  result.add "  1  the input is not valid base64\n"
  result.add "  2  usage error\n"

proc parseOptions*(args: seq[string]): Options =
  ## Decides everything without printing or exiting.
  result = Options(status: ok, command: encodeCommand, flavour: autoFlavour, padding: true)
  var position = 0
  var afterDoubleDash = false
  var sawCommand = false

  while position < args.len:
    let argument = args[position]
    inc position

    if not afterDoubleDash and argument == "--":
      afterDoubleDash = true
      continue

    if not afterDoubleDash and argument.len > 1 and argument[0] == '-':
      case argument
      of "-h", "--help":
        result.status = helpShown
        return
      of "-V", "--version":
        result.status = versionShown
        return
      of "--url":
        result.flavour = urlFlavour
        continue
      of "--no-padding":
        result.padding = false
        continue
      of "--standard":
        result.flavour = standardFlavour
        continue
      else:
        result.status = usageError
        result.message = "unknown option: " & argument
        return

    if not sawCommand:
      case argument
      of "encode":
        result.command = encodeCommand
      of "decode":
        result.command = decodeCommand
      else:
        result.status = usageError
        result.message = "unknown command: " & argument
        return
      sawCommand = true
      continue

    if result.value.len > 0:
      result.status = usageError
      result.message = "unexpected extra argument: " & argument
      return
    result.value = argument

  if not sawCommand:
    result.status = usageError
    result.message = "missing command (encode or decode)"
