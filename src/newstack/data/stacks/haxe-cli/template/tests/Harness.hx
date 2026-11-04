package;

/** Three lines of test harness — no framework, no dependencies. **/
class Harness {
  public static var passed = 0;
  public static var failed = 0;

  public static function check(label:String, condition:Bool):Void {
    if (condition) {
      passed++;
      Sys.println('ok   $label');
    } else {
      failed++;
      Sys.println('FAIL $label');
    }
  }

  public static function equal(label:String, got:Dynamic, want:Dynamic):Void {
    var ok = Std.string(got) == Std.string(want);
    check(ok ? label : '$label (got ${Std.string(got)}, want ${Std.string(want)})', ok);
  }

  public static function finish():Void {
    Sys.println('');
    Sys.println('checks: ${passed + failed}, passed: $passed, failed: $failed');
    Sys.exit(failed == 0 ? 0 : 1);
  }
}
