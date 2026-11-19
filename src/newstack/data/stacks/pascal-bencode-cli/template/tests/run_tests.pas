program run_tests;
{$mode objfpc}{$H+}
uses bencode, SysUtils;

var
  passed, failed: Integer;

procedure check(name: string; ok: Boolean);
begin
  if ok then Inc(passed) else begin Inc(failed); WriteLn('FAIL ', name); end;
end;

procedure check_text(name: string; actual, expected: AnsiString);
begin
  check(name, actual = expected);
  if actual <> expected then
  begin
    WriteLn('  got      ', actual);
    WriteLn('  expected ', expected);
  end;
end;

var
  v: PBencode;
  enc: AnsiString;
begin
  passed := 0; failed := 0;

  check('decode int', Decode('i42e', v));
  if v <> nil then check_text('encode int', Encode(v), 'i42e');

  check('decode str', Decode('4:spam', v));
  if v <> nil then check_text('encode str', Encode(v), '4:spam');

  check('decode list', Decode('li1ei2ee', v));
  if v <> nil then check_text('encode list', Encode(v), 'li1ei2ee');

  check('decode dict sorted', Decode('d3:fooi1ee', v));
  if v <> nil then check_text('encode dict', Encode(v), 'd3:fooi1ee');

  check('canonical reorder', Decode('d1:bi2e1:ai1ee', v) and (Encode(v) = 'd1:ai1e1:bi2ee'));

  check('invalid fails', not Decode('i42', v));

  WriteLn('checks: ', passed + failed, ', passed: ', passed, ', failed: ', failed);
  if failed = 0 then Halt(0) else Halt(1);
end.
