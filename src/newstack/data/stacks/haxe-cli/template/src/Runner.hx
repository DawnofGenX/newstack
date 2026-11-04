package;

import Options.Outcome;
import Options.OptionParser;

typedef Reading = {
  var label:String;
  var counts:TextStat.Counts;
}

/** Everything the runner needs from the outside world, so tests can fake it. **/
interface Io {
  function readFileBytes(path:String):haxe.io.Bytes;
  function readStdinBytes():haxe.io.Bytes;
}

class RealIo implements Io {
  public function new() {}

  public function readFileBytes(path:String):haxe.io.Bytes {
    return sys.io.File.getBytes(path);
  }

  public function readStdinBytes():haxe.io.Bytes {
    return Sys.stdin().readAll();
  }
}

class Runner {
  public static function digits(value:Int):Int {
    var text = Std.string(value);
    return text.length;
  }

  /**
    wc's column width, measured rather than guessed: a lone operand is never
    padded, any pipeline operand forces seven columns, and otherwise the width is
    the digit count of the byte total.
  **/
  static function figureWidth(operands:Int, figures:Int, total:TextStat.Counts, hasStream:Bool):Int {
    if (operands == 1 && figures == 1) return 0;
    if (hasStream) return 7;
    return digits(total.bytes);
  }

  static function countFigures(options:Options):Int {
    var figures = 0;
    if (options.lines) figures++;
    if (options.words) figures++;
    if (options.bytes) figures++;
    return figures;
  }

  static function printRow(out:StringBuf, options:Options, counts:TextStat.Counts, width:Int, label:String):Void {
    var cells:Array<String> = [];
    if (options.lines) cells.push(Std.string(counts.lines));
    if (options.words) cells.push(Std.string(counts.words));
    if (options.bytes) cells.push(Std.string(counts.bytes));
    var line = new StringBuf();
    for (index in 0...cells.length) {
      if (index > 0) line.add(" ");
      var cell = cells[index];
      if (width > cell.length) {
        line.add(StringTools.lpad(cell, " ", width));
      } else {
        line.add(cell);
      }
    }
    if (label != "") line.add(" " + label);
    out.add(line.toString() + "\n");
  }

  public static function run(program:String, args:Array<String>, io:Io, out:StringBuf, err:StringBuf):Int {
    var outcome = OptionParser.parse(args);
    switch (outcome) {
      case Help:
        out.add(OptionParser.usage(program));
        return 0;
      case Version:
        out.add('$program ${OptionParser.VERSION}\n');
        return 0;
      case Usage(reason):
        err.add('$program: $reason\n');
        err.add(OptionParser.usage(program));
        return 2;
      case Run(options):
        var operands = options.operands.copy();
        var implicit = operands.length == 0;
        if (implicit) operands = ["-"];

        var readings:Array<Reading> = [];
        var failed = false;
        var hasStream = implicit;
        for (operand in operands) {
          if (operand == "-") hasStream = true;
          try {
            var bytes = operand == "-" ? io.readStdinBytes() : io.readFileBytes(operand);
            var label = implicit ? "" : operand;
            readings.push({label: label, counts: TextStat.count(bytes)});
          } catch (error:Dynamic) {
            failed = true;
            err.add('$program: $operand: No such file or directory\n');
          }
        }

        var total:TextStat.Counts = {lines: 0, words: 0, bytes: 0};
        for (reading in readings) total = TextStat.add(total, reading.counts);
        var width = figureWidth(operands.length, countFigures(options), total, hasStream);

        for (reading in readings) {
          printRow(out, options, reading.counts, width, reading.label);
        }
        if (operands.length > 1) {
          printRow(out, options, total, width, "total");
        }
        return failed ? 1 : 0;
    }
    return 0;
  }
}
