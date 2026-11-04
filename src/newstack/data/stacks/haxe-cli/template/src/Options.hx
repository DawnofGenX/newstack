package;

enum Outcome {
  Run(options:Options);
  Help;
  Version;
  Usage(reason:String);
}

typedef Options = {
  var lines:Bool;
  var words:Bool;
  var bytes:Bool;
  var operands:Array<String>;
}

/** Parses wc's option grammar by hand: clusters, long forms, and `--`. **/
class OptionParser {
  public static inline var VERSION = "0.1.0";

  public static function usage(program:String):String {
    return 'Usage: $program [OPTION]... [FILE]...\n'
      + 'Print newline, word, and byte counts for each FILE.\n'
      + 'With no FILE, or when FILE is -, read standard input.\n\n'
      + '  -l, --lines   print the newline counts\n'
      + '  -w, --words   print the word counts\n'
      + '  -c, --bytes   print the byte counts\n'
      + '  -h, --help    display this help and exit\n'
      + '      --version  output version information and exit\n';
  }

  static function empty():Options {
    return {lines: false, words: false, bytes: false, operands: []};
  }

  public static function parse(args:Array<String>):Outcome {
    var options = empty();
    var i = 0;
    var onlyOperands = false;
    while (i < args.length) {
      var arg = args[i];
      if (onlyOperands || arg == "-" || !StringTools.startsWith(arg, "-")) {
        options.operands.push(arg);
      } else if (arg == "--") {
        onlyOperands = true;
      } else if (arg == "--help" || arg == "-h") {
        return Help;
      } else if (arg == "--version") {
        return Version;
      } else if (StringTools.startsWith(arg, "--")) {
        switch (arg) {
          case "--lines": options.lines = true;
          case "--words": options.words = true;
          case "--bytes": options.bytes = true;
          default: return Usage('unrecognized option: $arg');
        }
      } else {
        // A cluster such as -lw, which wc accepts.
        for (j in 1...arg.length) {
          switch (arg.charAt(j)) {
            case "l": options.lines = true;
            case "w": options.words = true;
            case "c": options.bytes = true;
            default: return Usage('invalid option -- ${arg.charAt(j)}');
          }
        }
      }
      i++;
    }
    if (!options.lines && !options.words && !options.bytes) {
      options.lines = true;
      options.words = true;
      options.bytes = true;
    }
    return Run(options);
  }
}
