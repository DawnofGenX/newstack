/// Just enough JSON to tell a string from a number.
module textstat.json;

import std.json : JSONException, JSONType, JSONValue, parseJSON;

enum TextKind
{
    invalid, /// the body is not a JSON object at all
    missing, /// valid object, but "text" is absent or not a string
    text     /// "text" is a string
}

TextKind readText(string body, out string text)
{
    text = "";
    JSONValue parsed;
    try
        parsed = parseJSON(body);
    catch (JSONException)
        return TextKind.invalid;
    if (parsed.type != JSONType.object)
        return TextKind.invalid;
    if ("text" !in parsed.object)
        return TextKind.missing;
    auto value = parsed.object["text"];
    if (value.type != JSONType.string)
        return TextKind.missing;
    text = value.str;
    return TextKind.text;
}

unittest
{
    string text;
    assert(readText(`{"text": "a b\nc\n"}`, text) == TextKind.text);
    assert(text == "a b\nc\n");
    assert(readText(`{"text": 42}`, text) == TextKind.missing);
    assert(readText(`{}`, text) == TextKind.missing);
    assert(readText(`{"other": "x"}`, text) == TextKind.missing);
    assert(readText(`nope`, text) == TextKind.invalid);
    assert(readText(``, text) == TextKind.invalid);
    assert(readText(`["text"]`, text) == TextKind.invalid);
    assert(readText(`{"text": "unterminated}`, text) == TextKind.invalid);
    // std.json stops at the end of the value, so trailing bytes are ignored.
    assert(readText(`{"text": "a"} trailing`, text) == TextKind.text);
    assert(text == "a");
    assert(readText(`{"text": "a\u00e9"}`, text) == TextKind.text);
    assert(text == "aé");
    assert(readText(`{"text": "\ud83d\ude42"}`, text) == TextKind.text);
    assert(text == "🙂");
}
