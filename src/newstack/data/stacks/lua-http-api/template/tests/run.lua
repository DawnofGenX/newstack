-- A framework-free suite: no busted, no luarocks, just the interpreter.
local function script_dir()
  local source = debug.getinfo(1, "S").source:sub(2)
  return source:match("^(.*)[/\\][^/\\]*$") or "."
end

package.path = script_dir() .. "/../src/?.lua;" .. package.path

local counts = require("counts")
local contract = require("contract")

local passed, failed = 0, 0

local function check(name, got, want)
  local same = got == want
  if same then
    passed = passed + 1
  else
    failed = failed + 1
    io.stderr:write(string.format("FAIL %s\n  got:  %s\n  want: %s\n", name, tostring(got), tostring(want)))
  end
end

local function counts_of(text)
  local result = counts.count_text(text)
  return string.format("%d/%d/%d", result.lines, result.words, result.bytes)
end

-- count_text ---------------------------------------------------------------
check("hello world", counts_of("hello world\n"), "1/2/12")
check("empty string", counts_of(""), "0/0/0")
check("blank lines", counts_of("\n\nx\n"), "3/1/4")
check("whitespace only", counts_of("  \t "), "0/0/4")
check("no newline", counts_of("abc"), "0/1/3")
check("utf8 bytes", counts_of("h\xc3\xa9llo w\xc3\xb6rld\n"), "1/2/14")
check("emoji", counts_of("\xf0\x9f\x99\x82\n"), "1/1/5")
check("tabs split words", counts_of("a\tb"), "0/2/3")
check("carriage returns are spaces", counts_of("a\r\nb"), "1/2/4")

-- notes on the counts table
do
  local ok, err = pcall(counts.count_text, 42)
  check("non-string is rejected", ok, false)
  check("the error names the type", tostring(err):find("got number", 1, true) ~= nil, true)
end

-- the route table ----------------------------------------------------------
local function route(method, path, query, body)
  local reply = contract.route(method, path, query, body)
  return string.format("%d %s", reply.status, reply.body)
end

check("health", route("GET", "/health", "", ""), '200 {"status":"ok"}')
check("greeting counted", route("GET", "/stats", "text=hello%20world%0A", ""),
  '200 {"text":"hello world\\n","lines":1,"words":2,"bytes":12}')
check("blank lines counted", route("GET", "/stats", "text=a%20b%0Ac%0A", ""),
  '200 {"text":"a b\\nc\\n","lines":2,"words":3,"bytes":6}')
check("plus decodes to a space", route("GET", "/stats", "text=a+b", ""),
  '200 {"text":"a b","lines":0,"words":2,"bytes":3}')
check("missing query", route("GET", "/stats", "", ""), '422 {"error":"missing_text"}')
check("posted text", route("POST", "/stats", "", '{"text":"a b\\nc\\n"}'),
  '200 {"text":"a b\\nc\\n","lines":2,"words":3,"bytes":6}')
check("posted empty text", route("POST", "/stats", "", '{"text":""}'),
  '200 {"text":"","lines":0,"words":0,"bytes":0}')
check("posted number is not text", route("POST", "/stats", "", '{"text":42}'),
  '422 {"error":"missing_text"}')
check("posted quoted number is text", route("POST", "/stats", "", '{"text":"42"}'),
  '200 {"text":"42","lines":0,"words":1,"bytes":2}')
check("broken json", route("POST", "/stats", "", "nope"), '422 {"error":"invalid_json"}')
-- Valid JSON that is not an object is still a document without a `text`
-- field: the same answer as any other body that carries no string.
check("json array has no text field", route("POST", "/stats", "", "[1,2]"), '422 {"error":"missing_text"}')
check("unknown route", route("GET", "/nope", "", ""),
  '404 {"error":"not_found","detail":"no route for GET /nope"}')
check("wrong method on health", route("DELETE", "/health", "", ""),
  '405 {"error":"method_not_allowed"}')
check("wrong method on stats", route("PUT", "/stats", "", ""), '405 {"error":"method_not_allowed"}')
check("quotes are escaped", route("POST", "/stats", "", '{"text":"a\\"b"}'),
  '200 {"text":"a\\"b","lines":0,"words":1,"bytes":3}')

io.stdout:write(string.format("%d checks passed, %d failed\n", passed, failed))
os.exit(failed == 0 and 0 or 1)
