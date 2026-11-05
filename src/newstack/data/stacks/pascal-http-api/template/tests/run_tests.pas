{ Exercises the pure contract and the counter without opening a socket. }
program run_tests;
{$mode objfpc}{$H+}

uses SysUtils, counts, jsonbody, contract;

var
  Passed: Integer = 0;
  Failed: Integer = 0;

procedure Check(const Name: AnsiString; Ok: Boolean);
begin
  if Ok then
    Inc(Passed)
  else
  begin
    Inc(Failed);
    WriteLn('FAIL ', Name);
  end;
end;

procedure Same(const Name, Got, Want: AnsiString);
begin
  if Got = Want then
    Inc(Passed)
  else
  begin
    Inc(Failed);
    WriteLn('FAIL ', Name, ' (got ', Got, ', want ', Want, ')');
  end;
end;

procedure CountsAre(const Name: AnsiString; const Text: AnsiString;
  Lines, Words, Bytes: Integer);
var
  Totals: TCounts;
begin
  Totals := CountText(Text);
  Check(Name + ': lines', Totals.Lines = Lines);
  Check(Name + ': words', Totals.Words = Words);
  Check(Name + ': bytes', Totals.Bytes = Bytes);
end;

procedure StatusIs(const Name, Method, Path, Query, Body: AnsiString; Status: Integer);
begin
  Check(Name + ': status', Route(Method, Path, Query, Body).Status = Status);
end;

function KindOf(const Body: AnsiString): AnsiString;
var
  Text: AnsiString;
begin
  case ReadTextBody(Body, Text) of
    tkInvalid: Result := 'invalid';
    tkMissing: Result := 'missing';
    tkText: Result := 'text:' + Text;
  end;
end;

procedure CountingTests;
begin
  CountsAre('empty input', '', 0, 0, 0);
  CountsAre('one line', 'hello world' + #10, 1, 2, 12);
  CountsAre('two lines', 'a b' + #10 + 'c' + #10, 2, 3, 6);
  CountsAre('blank lines', #10 + #10 + 'x' + #10, 3, 1, 4);
  CountsAre('spaces only', '  ' + #9 + ' ', 0, 0, 4);
  CountsAre('no trailing newline', 'abc', 0, 1, 3);
  CountsAre('utf-8 payload', 'h' + #$C3#$A9 + 'llo w' + #$C3#$B6 + 'rld' + #10, 1, 2, 14);
  CountsAre('emoji', #$F0#$9F#$99#$82 + #10, 1, 1, 5);
end;

procedure JsonTests;
begin
  Same('a string member is read', KindOf('{"text":"a b\nc\n"}'), 'text:a b' + #10 + 'c' + #10);
  Same('a number is missing', KindOf('{"text":42}'), 'missing');
  Same('null is missing', KindOf('{"text":null}'), 'missing');
  Same('an object is missing', KindOf('{"text":{"a":1}}'), 'missing');
  Same('an absent member is missing', KindOf('{"body":"x"}'), 'missing');
  Same('an empty object is missing', KindOf('{}'), 'missing');
  Same('a bare word is invalid', KindOf('nope'), 'invalid');
  Same('an array is invalid', KindOf('["text"]'), 'invalid');
  Same('an unterminated string is invalid', KindOf('{"text":"a}'), 'invalid');
  Same('other members are skipped',
    KindOf('{"n":1,"text":"x","f":true,"o":{"k":[1,2]}}'), 'text:x');
  Same('an escaped unicode member is decoded',
    KindOf('{"text":"h\u00e9llo"}'), 'text:h' + #$C3#$A9 + 'llo');
  Same('a surrogate pair is decoded',
    KindOf('{"text":"\ud83d\ude42\n"}'), 'text:' + #$F0#$9F#$99#$82 + #10);
  Same('raw utf-8 passes through',
    KindOf('{"text":"h' + #$C3#$A9 + 'llo"}'), 'text:h' + #$C3#$A9 + 'llo');
  Same('trailing data is invalid', KindOf('{"text":"a"} trailing'), 'invalid');
end;

procedure ContractTests;
var
  Reply: TReply;
begin
  StatusIs('health', 'GET', '/health', '', '', 200);
  Same('health body', Route('GET', '/health', '', '').Body, '{"status":"ok"}');

  Reply := Route('GET', '/stats', 'text=hello%20world%0A', '');
  Same('a query is counted: status', IntToStr(Reply.Status), '200');
  Same('a query is counted: body', Reply.Body,
    '{"text":"hello world\n","lines":1,"words":2,"bytes":12}');

  Same('plus is a space', Route('GET', '/stats', 'text=hello+world', '').Body,
    '{"text":"hello world","lines":0,"words":2,"bytes":11}');

  Same('an empty value is zero', Route('GET', '/stats', 'text=', '').Body,
    '{"text":"","lines":0,"words":0,"bytes":0}');

  Reply := Route('POST', '/stats', '', '{"text":"a b\nc\n"}');
  Same('a body is counted: status', IntToStr(Reply.Status), '200');
  Same('a body is counted: body', Reply.Body,
    '{"text":"a b\nc\n","lines":2,"words":3,"bytes":6}');

  Same('utf-8 bytes, not characters',
    Route('POST', '/stats', '', '{"text":"h\u00e9llo w\u00f6rld\n"}').Body,
    '{"text":"h' + #$C3#$A9 + 'llo w' + #$C3#$B6 + 'rld\n","lines":1,"words":2,"bytes":14}');

  StatusIs('no text', 'GET', '/stats', '', '', 422);
  Same('no text is missing_text', Route('GET', '/stats', '', '').Body,
    '{"error":"missing_text"}');
  StatusIs('a number is rejected', 'POST', '/stats', '', '{"text":42}', 422);
  Same('a number is missing_text', Route('POST', '/stats', '', '{"text":42}').Body,
    '{"error":"missing_text"}');
  StatusIs('broken JSON is rejected', 'POST', '/stats', '', 'nope', 422);
  Same('broken JSON is invalid_json', Route('POST', '/stats', '', 'nope').Body,
    '{"error":"invalid_json"}');
  StatusIs('a known path, wrong method', 'DELETE', '/health', '', '', 405);
  Same('405 body', Route('DELETE', '/health', '', '').Body,
    '{"error":"method_not_allowed"}');
  StatusIs('an unknown path', 'GET', '/nope', '', '', 404);
  Same('404 names the route', Route('GET', '/nope', '', '').Body,
    '{"error":"not_found","detail":"no route for GET /nope"}');
  Same('quotes survive both ways',
    Route('POST', '/stats', '', '{"text":"a\"quote\""}').Body,
    '{"text":"a\"quote\"","lines":0,"words":1,"bytes":8}');
end;

begin
  CountingTests;
  JsonTests;
  ContractTests;
  WriteLn('checks: ', Passed + Failed, ', passed: ', Passed, ', failed: ', Failed);
  if Failed > 0 then
    Halt(1);
end.
