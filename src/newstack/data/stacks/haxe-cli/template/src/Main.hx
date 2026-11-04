package;

class Main {
  public static function main() {
    var program = "{{ npm_name }}";
    var out = new StringBuf();
    var err = new StringBuf();
    var code = Runner.run(program, Sys.args(), new Runner.RealIo(), out, err);
    Sys.stdout().writeString(out.toString());
    Sys.stderr().writeString(err.toString());
    Sys.exit(code);
  }
}
