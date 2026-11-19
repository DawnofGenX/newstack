program bencodecli;
{$mode objfpc}{$H+}
uses BaseUnix, SysUtils, bencode;

function ReadAll(fd: cint): AnsiString;
var
  buffer: array[0..65535] of Byte;
  n: TSsize;
  total: SizeInt;
begin
  Result := '';
  total := 0;
  repeat
    n := fpRead(fd, buffer, SizeOf(buffer));
    if n > 0 then
    begin
      SetLength(Result, total + n);
      Move(buffer, Result[total + 1], n);
      Inc(total, n);
    end;
  until n <= 0;
end;

function ReadPath(const path_: string; out ok: Boolean): AnsiString;
var
  fd: cint;
begin
  ok := False;
  Result := '';
  if path_ = '-' then
  begin
    Result := ReadAll(0);
    ok := True;
    Exit;
  end;
  fd := fpOpen(path_, O_RDONLY);
  if fd < 0 then Exit;
  Result := ReadAll(fd);
  fpClose(fd);
  ok := True;
end;

var
  i: Integer;
  ok: Boolean;
  raw: AnsiString;
  v: PBencode;
  trimmed: AnsiString;
begin
  if (ParamCount >= 1) and ((ParamStr(1) = '--help') or (ParamStr(1) = '-h')) then
  begin
    WriteLn('Usage: {{ npm_name }} [FILE]');
    WriteLn('Decode and re-encode bencode with canonical key ordering.');
    Halt(0);
  end;
  if ParamCount > 1 then
  begin
    WriteLn(StdErr, 'usage: {{ npm_name }} [FILE]');
    Halt(2);
  end;

  if ParamCount = 0 then
  begin
    raw := ReadAll(0);
  end
  else
  begin
    raw := ReadPath(ParamStr(1), ok);
    if not ok then
    begin
      WriteLn(StdErr, 'error: cannot open ''', ParamStr(1), '''');
      Halt(1);
    end;
  end;

  trimmed := Trim(raw);
  if not Decode(trimmed, v) then
  begin
    WriteLn(StdErr, 'error: invalid bencode');
    Halt(1);
  end;
  Write(Encode(v));
  WriteLn;
  Halt(0);
end.
