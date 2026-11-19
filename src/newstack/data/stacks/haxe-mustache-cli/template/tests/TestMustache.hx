package;

class TestMustache {
  public static function run():Void {
    Harness.equal("variable", Mustache.render("Hello {{!name}}", {"name":"World"}), "Hello World");
    Harness.equal("escape", Mustache.render("{{!x}}", {"x":"a<b"}), "a&lt;b");
    Harness.equal("unescape triple", Mustache.render("{{!{x}}}", {"x":"<b>"}), "<b>");
    Harness.equal("unescape amp", Mustache.render("{{!&x}}", {"x":"<b>"}), "<b>");
    Harness.equal("section array", Mustache.render("{{!#items}}{{!.}} {{!/items}}", {"items":["hi","hi"]}), "hi hi ");
    Harness.equal("inverted", Mustache.render("{{!^items}}empty{{!/items}}", {"items":[]}), "empty");
    Harness.equal("comment", Mustache.render("a{{!! c }}b", {}), "ab");
    Harness.equal("missing", Mustache.render("{{!x}}", {}), "");
    Harness.equal("known", Mustache.render("Name: {{!name}}\nItems: {{!#items}}{{!.}}{{!/items}}", {"name":"Bob","items":[1,2,3]}), "Name: Bob\nItems: 123");
    Harness.equal("nested path", Mustache.render("{{!a.b}}", {"a":{"b":"x.y"}}), "x.y");
    var partials = new Map<String,String>();
    partials.set("p", "[{{!.}}]");
    Harness.equal("partial", Mustache.render("a{{!>p}}b", 1, partials), "a[1]b");
  }
}
