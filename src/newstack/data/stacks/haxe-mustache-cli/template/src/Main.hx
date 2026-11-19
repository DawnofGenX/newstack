package;

class Main {
  static function main() {
    var program = "mustache";
    var args = Sys.args();
    var code = Runner.run(program, args);
    Sys.exit(code);
  }
}
