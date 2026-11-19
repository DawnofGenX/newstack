package;

class Main {
  public static function main() {
    var args = Sys.args();
    var file = null;
    var select = null;
    var count = false;
    var i = 0;
    while (i < args.length) {
      var a = args[i];
      if (a == "--select") {
        select = args[i + 1];
        i += 2;
        continue;
      } else if (a == "--count") {
        count = true;
        i++;
        continue;
      } else if (a == "-h" || a == "--help") {
        Sys.println("Usage: {{ npm_name }} [OPTION]... [FILE]...");
        Sys.println("  --select COLS  select columns (comma separated)");
        Sys.println("  --count        print row count");
        Sys.exit(0);
      } else if (StringTools.startsWith(a, "-")) {
        Sys.stderr().writeString("{{ npm_name }}: unknown option: " + a + "\n");
        Sys.exit(2);
      } else {
        file = a;
        i++;
      }
    }
    if (file == null) {
      Sys.println("Usage: {{ npm_name }} [OPTION]... [FILE]...");
      Sys.exit(2);
    }
    var text:String = null;
    try {
      text = sys.io.File.getContent(file);
    } catch (e:Dynamic) {
      Sys.stderr().writeString("{{ npm_name }}: cannot open '" + file + "'\n");
      Sys.exit(1);
    }
    var table = Csv.parse(text);
    if (count) {
      Sys.println(Std.string(table.rows.length));
      Sys.exit(0);
    }
    if (select != null) {
      table = Csv.select(table, select.split(","));
    }
    Sys.print(Csv.render(table));
    Sys.exit(0);
  }
}
