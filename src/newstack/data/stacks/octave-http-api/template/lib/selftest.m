function failures = selftest()
%SELFTEST Framework-free checks over the counting, JSON and routing layers.
  failures = 0;
  total = 0;

  total = total + 1;
  failures = failures + check('empty text counts zero', counted(uint8([]), [0 0 0]));

  total = total + 1;
  failures = failures + check('ascii sentence', counted(uint8(sprintf('hello world\n')), [1 2 12]));

  total = total + 1;
  failures = failures + check('utf-8 counts bytes not characters', ...
    counted(uint8([104 195 169 108 108 111 32 119 195 182 114 108 100 10]), [1 2 14]));

  total = total + 1;
  failures = failures + check('all six separators split words', ...
    counted(uint8([97 32 97 9 97 10 97 13 97 11 97 12 97]), [1 7 13]));

  total = total + 1;
  [kind, text] = jsonread(uint8('{"text":"a b\nc\n"}'));
  failures = failures + check('json keeps the text member', ...
    strcmp(kind, 'text') && isequal(text, uint8(sprintf('a b\nc\n'))));

  total = total + 1;
  [kind, ~] = jsonread(uint8('{}'));
  failures = failures + check('missing text is reported', strcmp(kind, 'missing'));

  total = total + 1;
  [kind, ~] = jsonread(uint8('{"text":42}'));
  failures = failures + check('a non-string text is invalid', strcmp(kind, 'invalid'));

  total = total + 1;
  [kind, ~] = jsonread(uint8('not json'));
  failures = failures + check('garbage is invalid', strcmp(kind, 'invalid'));

  total = total + 1;
  [kind, text] = jsonread(uint8('{"text":"\u00e9\u00e8"}'));
  failures = failures + check('escapes decode to utf-8', ...
    strcmp(kind, 'text') && isequal(text, uint8([195 169 195 168])));

  total = total + 1;
  [kind, text] = jsonread(uint8('{"text":"\uD83D\uDE00"}'));
  failures = failures + check('surrogate pairs combine', ...
    strcmp(kind, 'text') && numel(text) == 4 && text(1) == 240);

  total = total + 1;
  [kind, text] = jsonread(uint8('{"meta":{"n":[1,2,{"x":true}]},"text":"x"}'));
  failures = failures + check('nested values are skipped', ...
    strcmp(kind, 'text') && isequal(text, uint8('x')));

  total = total + 1;
  [kind, text] = jsonread(uint8('{"text":"a","text":"b"}'));
  failures = failures + check('the last text member wins', ...
    strcmp(kind, 'text') && isequal(text, uint8('b')));

  total = total + 1;
  [kind, ~] = jsonread(uint8('{"text":"x"} trailing'));
  failures = failures + check('trailing garbage is invalid', strcmp(kind, 'invalid'));

  total = total + 1;
  failures = failures + check('percent escapes decode to bytes', ...
    isequal(percent_decode('h%C3%A9llo'), uint8([104 195 169 108 108 111])));

  total = total + 1;
  failures = failures + check('plus decodes to a space', ...
    isequal(percent_decode('a+b'), uint8([97 32 98])));

  total = total + 1;
  failures = failures + check('a truncated escape stays literal', ...
    isequal(percent_decode('50%'), uint8([53 48 37])));

  total = total + 1;
  failures = failures + check('json quoting escapes a newline', ...
    isequal(json_quote(uint8(sprintf('a\nb'))), uint8('"a\nb"')));

  total = total + 1;
  failures = failures + check('json quoting escapes a quote', ...
    isequal(json_quote(uint8('a"b')), uint8('"a\"b"')));

  total = total + 1;
  [status, body] = route('GET', '/health', uint8([]));
  failures = failures + check('health answers 200', ...
    status == 200 && isequal(body, uint8('{"status":"ok"}')));

  total = total + 1;
  [status, body] = route('GET', '/stats?text=hello%20world%0A', uint8([]));
  failures = failures + check('a query is counted', ...
    status == 200 && isequal(body, uint8('{"text":"hello world\n","lines":1,"words":2,"bytes":12}')));

  total = total + 1;
  [status, ~] = route('GET', '/stats', uint8([]));
  failures = failures + check('a missing query parameter is 422', status == 422);

  total = total + 1;
  [status, body] = route('POST', '/stats', uint8('{"text":"a b\nc\n"}'));
  failures = failures + check('a json body is counted', ...
    status == 200 && isequal(body, uint8('{"text":"a b\nc\n","lines":2,"words":3,"bytes":6}')));

  total = total + 1;
  [status, body] = route('POST', '/stats', uint8('{}'));
  failures = failures + check('a body without text is 422 missing_text', ...
    status == 422 && isequal(body, uint8('{"error":"missing_text"}')));

  total = total + 1;
  [status, body] = route('POST', '/stats', uint8('{"text":1}'));
  failures = failures + check('a numeric text is 422 invalid_json', ...
    status == 422 && isequal(body, uint8('{"error":"invalid_json"}')));

  total = total + 1;
  [status, body] = route('GET', '/nope', uint8([]));
  failures = failures + check('an unknown route is 404 with a detail', ...
    status == 404 && isequal(body, uint8('{"error":"not_found","detail":"no route for GET /nope"}')));

  total = total + 1;
  [status, body] = route('DELETE', '/health', uint8([]));
  failures = failures + check('a wrong method is 405', ...
    status == 405 && isequal(body, uint8('{"error":"method_not_allowed"}')));

  total = total + 1;
  [status, ~] = route('GET', '/stats?x=1&text=one&text=two', uint8([]));
  failures = failures + check('the first query parameter wins', status == 200);

  printf('checks: %d, failed: %d\n', total, failures);
  if failures == 0
    printf('checks: all passed\n');
  end
end

function ok = counted(raw, want)
  [lines, words, nbytes] = counts(raw);
  ok = isequal([lines words nbytes], want);
end

function bad = check(name, ok)
  if ok
    printf('ok %s\n', name);
    bad = 0;
  else
    printf('FAIL %s\n', name);
    bad = 1;
  end
end
