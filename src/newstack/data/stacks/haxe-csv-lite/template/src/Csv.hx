package;

typedef CsvTable = {
  header:Array<String>,
  rows:Array<Array<String>>
};

class Csv {
  public static function parse(text:String):CsvTable {
    var header:Array<String> = null;
    var rows = new Array<Array<String>>();
    var current = new Array<String>();
    var field = new StringBuf();
    var inQuotes = false;
    var atFieldStart = true;
    var i = 0;
    var len = text.length;
    function endField() {
      current.push(field.toString());
      field = new StringBuf();
      atFieldStart = true;
    }
    function endRow() {
      // skip completely empty trailing row
      if (current.length == 1 && current[0] == "" && rows.length == 0 && header == null) {
        // keep? skip empty leading
      }
      if (header == null) {
        header = current;
      } else {
        rows.push(current);
      }
      current = new Array<String>();
    }
    while (i < len) {
      var c = text.charAt(i);
      if (inQuotes) {
        if (c == "\"") {
          if (i + 1 < len && text.charAt(i + 1) == "\"") {
            field.addChar('"'.code);
            i++;
          } else {
            inQuotes = false;
          }
        } else {
          field.add(c);
        }
      } else {
        if (atFieldStart && c == "\"") {
          inQuotes = true;
          atFieldStart = false;
        } else if (c == ",") {
          endField();
        } else if (c == "\n") {
          endField();
          endRow();
        } else if (c == "\r") {
          // ignore
        } else {
          field.add(c);
          atFieldStart = false;
        }
      }
      i++;
    }
    // final field/row if any content
    if (field.toString() != "" || current.length > 0 || (header != null)) {
      // push last field if row not empty
      if (current.length > 0 || field.toString() != "") {
        current.push(field.toString());
      }
      if (current.length > 0) {
        if (header == null) header = current; else rows.push(current);
      }
    }
    if (header == null) header = new Array<String>();
    return {header: header, rows: rows};
  }

  public static function select(table:CsvTable, cols:Array<String>):CsvTable {
    var idx = new Array<Int>();
    for (c in cols) {
      var i = 0;
      var found = -1;
      for (h in table.header) {
        if (h == c) { found = i; break; }
        i++;
      }
      idx.push(found);
    }
    var newHeader = cols.copy();
    var newRows = new Array<Array<String>>();
    for (r in table.rows) {
      var nr = new Array<String>();
      for (i in idx) {
        nr.push(i >= 0 && i < r.length ? r[i] : "");
      }
      newRows.push(nr);
    }
    return {header: newHeader, rows: newRows};
  }

  public static function render(table:CsvTable):String {
    var buf = new StringBuf();
    buf.add(table.header.join(","));
    buf.add("\n");
    for (r in table.rows) {
      buf.add(r.join(","));
      buf.add("\n");
    }
    return buf.toString();
  }
}
