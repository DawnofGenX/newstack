package;

class CsvTest {
  public static function run():Void {
    var t = Csv.parse("name,age\nalice,30\nbob,25\n");
    Harness.equal("header", t.header.join(","), "name,age");
    Harness.equal("rows", t.rows.length, 2);
    Harness.equal("first name", t.rows[0][0], "alice");
    Harness.equal("second age", t.rows[1][1], "25");

    var s = Csv.select(t, ["age"]);
    Harness.equal("select header", s.header.join(","), "age");
    Harness.equal("select first", s.rows[0][0], "30");

    var r = Csv.render(s);
    Harness.check("render contains 30", r.indexOf("30") >= 0);
  }
}
