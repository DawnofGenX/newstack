package;

import Options.Outcome;
import Options.OptionParser;

class OptionsTest {
  public static function run():Void {
    switch (OptionParser.parse([])) {
      case Run(o):
        Harness.check("no flags means all three figures", o.lines && o.words && o.bytes);
        Harness.equal("no flags means no operands", o.operands.length, 0);
      default:
        Harness.check("no flags is a run", false);
    }

    switch (OptionParser.parse(["-lw"])) {
      case Run(o):
        Harness.check("clustered flags apply both", o.lines && o.words && !o.bytes);
      default:
        Harness.check("cluster parses", false);
    }

    switch (OptionParser.parse(["--bytes", "a.txt"])) {
      case Run(o):
        Harness.check("long flag", o.bytes && !o.lines && !o.words);
        Harness.equal("operand kept", o.operands[0], "a.txt");
      default:
        Harness.check("long flag parses", false);
    }

    switch (OptionParser.parse(["-l", "-", "b.txt"])) {
      case Run(o):
        Harness.equal("dash stays an operand", o.operands.join(","), "-,b.txt");
      default:
        Harness.check("dash parses", false);
    }

    switch (OptionParser.parse(["--", "-l"])) {
      case Run(o):
        Harness.equal("-- stops option parsing", o.operands.join(","), "-l");
      default:
        Harness.check("-- parses", false);
    }

    switch (OptionParser.parse(["--help"])) {
      case Help: Harness.check("--help asks for help", true);
      default: Harness.check("--help asks for help", false);
    }

    switch (OptionParser.parse(["-h"])) {
      case Help: Harness.check("-h asks for help", true);
      default: Harness.check("-h asks for help", false);
    }

    switch (OptionParser.parse(["--version"])) {
      case Version: Harness.check("--version asks for the version", true);
      default: Harness.check("--version asks for the version", false);
    }

    switch (OptionParser.parse(["--bogus"])) {
      case Usage(reason): Harness.check('unknown long option is a usage error ($reason)', reason.indexOf("--bogus") >= 0);
      default: Harness.check("unknown long option is a usage error", false);
    }

    switch (OptionParser.parse(["-z"])) {
      case Usage(reason): Harness.check('unknown short option is a usage error ($reason)', reason.indexOf("z") >= 0);
      default: Harness.check("unknown short option is a usage error", false);
    }
  }
}
