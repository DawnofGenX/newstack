package;

enum Outcome {
  Run(templatePath:String, dataPath:String);
  Help;
  Version;
  Usage(reason:String);
}

class OptionParser {
  public static inline var VERSION = "0.1.0";

  public static function usage(program:String):String {
    return 'Usage: $program [OPTION]... TEMPLATE [DATA]\n'
      + 'Render a Mustache TEMPLATE with a JSON DATA file.\n'
      + 'With no DATA, or when DATA is -, read JSON from standard input.\n'
      + 'TEMPLATE of - reads the template from standard input.\n\n'
      + '  -h, --help     display this help and exit\n'
      + '      --version  output version information and exit\n';
  }

  public static function parse(args:Array<String>):Outcome {
    var positional:Array<String> = [];
    var i = 0;
    while (i < args.length) {
      var arg = args[i];
      if (arg == "--help" || arg == "-h") return Help;
      else if (arg == "--version") return Version;
      else if (StringTools.startsWith(arg, "-") && arg != "-") {
        return Usage('unrecognized option: $arg');
      } else {
        positional.push(arg);
      }
      i++;
    }
    if (positional.length == 0) return Usage('missing TEMPLATE');
    var templatePath = positional[0];
    var dataPath = positional.length > 1 ? positional[1] : "-";
    if (positional.length > 2) return Usage('too many arguments');
    return Run(templatePath, dataPath);
  }
}
