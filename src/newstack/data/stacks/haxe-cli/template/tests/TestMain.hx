package;

class TestMain {
  public static function main() {
    CountsTest.run();
    OptionsTest.run();
    RunnerTest.runTests();
    Harness.finish();
  }
}
