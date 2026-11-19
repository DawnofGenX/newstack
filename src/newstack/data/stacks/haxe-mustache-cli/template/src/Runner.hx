package;

import Options.OptionParser;
import Options.Outcome;

import haxe.Json;

class Runner {
  public static function run(program:String, args:Array<String>):Int {
    var outcome = OptionParser.parse(args);
    return switch (outcome) {
      case Help:
        Sys.print(OptionParser.usage(program));
        0;
      case Version:
        Sys.print(OptionParser.VERSION + "\n");
        0;
      case Usage(reason):
        Sys.stderr().writeString(program + ": " + reason + "\n" + OptionParser.usage(program));
        2;
      case Run(templatePath, dataPath):
        var templateText:String;
        try {
          if (templatePath == "-") templateText = readAllStdin();
          else templateText = sys.io.File.getContent(templatePath);
        } catch (e:Dynamic) {
          Sys.stderr().writeString(program + ": cannot read template '" + templatePath + "': " + Std.string(e) + "\n");
          return 1;
        }
        var dataText:String;
        try {
          if (dataPath == "-") dataText = readAllStdin();
          else dataText = sys.io.File.getContent(dataPath);
        } catch (e:Dynamic) {
          Sys.stderr().writeString(program + ": cannot read data '" + dataPath + "': " + Std.string(e) + "\n");
          return 1;
        }
        var data:Dynamic;
        try {
          data = haxe.Json.parse(dataText);
        } catch (e:Dynamic) {
          Sys.stderr().writeString(program + ": invalid JSON data: " + Std.string(e) + "\n");
          return 1;
        }
        var out = Mustache.render(templateText, data);
        Sys.print(out);
        0;
    }
  }

  static function readAllStdin():String {
    var buf = new StringBuf();
    var stdin = Sys.stdin();
    try {
      while (true) {
        var line = stdin.readLine();
        buf.add(line);
        buf.add("\n");
      }
    } catch (e:Dynamic) {
      // EOF
    }
    return buf.toString();
  }
}
