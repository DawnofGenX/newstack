package;

import haxe.Json;

class Mustache {
  public static function render(template:String, data:Dynamic, ?partials:Map<String, String>):String {
    var nodes = new Parser(template).parse();
    var ctx = new Context(data);
    return renderNodes(nodes, ctx, partials);
  }

  static function renderNodes(nodes:Array<Node>, ctx:Context, partials:Map<String, String>):String {
    var buf = new StringBuf();
    for (node in nodes) {
      switch (node) {
        case Text(s): buf.add(s);
        case Var(name, escape):
          var value = ctx.lookup(name);
          var text = value == null ? "" : Std.string(value);
          if (escape) buf.add(htmlEscape(text)); else buf.add(text);
        case Section(name, inverted, children):
          var value = ctx.lookup(name);
          if (inverted) {
            if (!isTruthy(value)) buf.add(renderNodes(children, ctx, partials));
          } else {
            if (Std.isOfType(value, Array)) {
              var arr:Array<Dynamic> = cast value;
              if (arr.length == 0) {
                // nothing
              } else {
                for (item in arr) {
                  ctx.push(item);
                  buf.add(renderNodes(children, ctx, partials));
                  ctx.pop();
                }
              }
            } else if (isTruthy(value)) {
              if (Std.isOfType(value, Bool)) {
                ctx.push(ctx.top());
                buf.add(renderNodes(children, ctx, partials));
                ctx.pop();
              } else {
                ctx.push(value);
                buf.add(renderNodes(children, ctx, partials));
                ctx.pop();
              }
            }
          }
        case Partial(name):
          var tmpl = null;
          if (partials != null && partials.exists(name)) tmpl = partials.get(name);
          if (tmpl == null) {
            try {
              tmpl = sys.io.File.getContent(name + ".mustache");
            } catch (e:Dynamic) {
              try { tmpl = sys.io.File.getContent(name); } catch (e2:Dynamic) { tmpl = ""; }
            }
          }
          if (tmpl != null) {
            var pnodes = new Parser(tmpl).parse();
            buf.add(renderNodes(pnodes, ctx, partials));
          }
        case Comment:
          // nothing
      }
    }
    return buf.toString();
  }

  static function isTruthy(value:Dynamic):Bool {
    if (value == null) return false;
    if (Std.isOfType(value, Bool)) return value;
    if (Std.isOfType(value, String)) return value != "";
    if (Std.isOfType(value, Int) || Std.isOfType(value, Float)) return value != 0;
    if (Std.isOfType(value, Array)) return (cast value : Array<Dynamic>).length > 0;
    return true;
  }

  static function htmlEscape(s:String):String {
    return s.split("&").join("&amp;")
            .split("<").join("&lt;")
            .split(">").join("&gt;")
            .split("\"").join("&quot;")
            .split("'").join("&#39;");
  }
}

class Context {
  public var stack:Array<Dynamic>;
  public function new(data:Dynamic) { stack = [data]; }
  public function push(v:Dynamic) stack.push(v);
  public function pop() { if (stack.length > 1) stack.pop(); }
  public function top():Dynamic return stack[stack.length - 1];

  public function lookup(name:String):Dynamic {
    if (name == "." || name == "") return top();
    var parts = name.split(".");
    for (i in 0...stack.length) {
      var ctx = stack[stack.length - 1 - i];
      if (hasPath(ctx, parts)) return resolvePath(ctx, parts);
    }
    return null;
  }

  static function hasPath(ctx:Dynamic, parts:Array<String>):Bool {
    var cur = ctx;
    for (part in parts) {
      if (cur == null) return false;
      if (Std.isOfType(cur, String) || Std.isOfType(cur, Bool) || Std.isOfType(cur, Int) || Std.isOfType(cur, Float) || Std.isOfType(cur, Array)) return false;
      if (!Reflect.hasField(cur, part)) return false;
      cur = Reflect.field(cur, part);
    }
    return true;
  }

  static function resolvePath(ctx:Dynamic, parts:Array<String>):Dynamic {
    var cur = ctx;
    for (part in parts) {
      if (cur == null) return null;
      cur = Reflect.field(cur, part);
    }
    return cur;
  }
}

enum Node {
  Text(s:String);
  Var(name:String, escape:Bool);
  Section(name:String, inverted:Bool, children:Array<Node>);
  Partial(name:String);
  Comment;
}

class Parser {
  var s:String;
  var pos:Int;
  var len:Int;
  public function new(template:String) {
    s = template;
    pos = 0;
    len = s.length;
  }
  public function parse():Array<Node> {
    return parseNodes(null);
  }
  function parseNodes(closeName:Null<String>):Array<Node> {
    var nodes:Array<Node> = [];
    var textBuf = new StringBuf();
    while (pos < len) {
      var tagStart = s.indexOf("{{", pos);
      if (tagStart == -1) {
        textBuf.add(s.substr(pos));
        pos = len;
        break;
      }
      textBuf.add(s.substr(pos, tagStart - pos));
      pos = tagStart;

      var unescape = false;
      if (pos + 2 < len && s.substr(pos, 3) == "{{{") {
        unescape = true;
        pos += 3;
      } else {
        pos += 2;
      }
      var endMarker = unescape ? "}}}" : "}}";
      var tagEnd = s.indexOf(endMarker, pos);
      if (tagEnd == -1) {
        textBuf.add(s.substr(tagStart));
        pos = len;
        break;
      }
      var inner = StringTools.trim(s.substr(pos, tagEnd - pos));
      pos = tagEnd + endMarker.length;

      if (inner.length > 0 && inner.charAt(0) == "/") {
        var name = StringTools.trim(inner.substr(1));
        // flush text
        var t = textBuf.toString();
        if (t != "") nodes.push(Text(t));
        textBuf = new StringBuf();
        if (closeName != null && name == closeName) {
          return nodes;
        }
        // mismatched close: ignore
        continue;
      }

      if (inner.length > 0 && inner.charAt(0) == "#") {
        var name = StringTools.trim(inner.substr(1));
        var t = textBuf.toString();
        if (t != "") nodes.push(Text(t));
        textBuf = new StringBuf();
        var children = parseNodes(name);
        nodes.push(Section(name, false, children));
        continue;
      }

      if (inner.length > 0 && inner.charAt(0) == "^") {
        var name = StringTools.trim(inner.substr(1));
        var t = textBuf.toString();
        if (t != "") nodes.push(Text(t));
        textBuf = new StringBuf();
        var children = parseNodes(name);
        nodes.push(Section(name, true, children));
        continue;
      }

      if (inner.length > 0 && inner.charAt(0) == "!") {
        // comment: ignore
        continue;
      }

      if (inner.length > 0 && inner.charAt(0) == ">") {
        var name = StringTools.trim(inner.substr(1));
        var t = textBuf.toString();
        if (t != "") nodes.push(Text(t));
        textBuf = new StringBuf();
        nodes.push(Partial(name));
        continue;
      }

      if (inner.length > 0 && inner.charAt(0) == "&") {
        var name = StringTools.trim(inner.substr(1));
        var t = textBuf.toString();
        if (t != "") nodes.push(Text(t));
        textBuf = new StringBuf();
        nodes.push(Var(name, false));
        continue;
      }

      // variable (possibly unescape via triple already)
      var t = textBuf.toString();
      if (t != "") nodes.push(Text(t));
      textBuf = new StringBuf();
      nodes.push(Var(inner, !unescape));
    }
    var t = textBuf.toString();
    if (t != "") nodes.push(Text(t));
    return nodes;
  }
}
