program run_tests;
{$mode objfpc}{$H+}
uses Classes, SysUtils, uuidgen, uuidopts, uuidrunner;
var Passed, Failed: Integer;

procedure Check(const Name: string; Condition: Boolean; const Detail: string);
begin
  if Condition then Inc(Passed)
  else
  begin
    Inc(Failed);
    WriteLn('FAIL ', Name);
    if Detail <> '' then WriteLn('     ', Detail);
  end;
end;

function Capture(const Args: array of string; out OutText, ErrText: string): Integer;
var OutStream, ErrStream: TMemoryStream;
begin
  OutStream := TMemoryStream.Create;
  ErrStream := TMemoryStream.Create;
  try
    Result := Run(Args, OutStream, ErrStream);
    SetLength(OutText, OutStream.Size);
    if OutStream.Size > 0 then Move(OutStream.Memory^, OutText[1], OutStream.Size);
    SetLength(ErrText, ErrStream.Size);
    if ErrStream.Size > 0 then Move(ErrStream.Memory^, ErrText[1], ErrStream.Size);
  finally
    OutStream.Free;
    ErrStream.Free;
  end;
end;

var U, V: TUuid; S: string; OutText, ErrText: string; Code: Integer;
begin
  Passed := 0;
  Failed := 0;

  U := NewUuidV4;
  S := FormatUuid(U);
  Check('canonical shape', (Length(S) = 36) and (S[9] = '-') and (S[14] = '-') and (S[19] = '-') and (S[24] = '-'), S);
  Check('version nibble is 4', Version(U) = 4, IntToStr(Version(U)));
  Check('variant is RFC 4122', Variant(U) = 2, IntToStr(Variant(U)));
  Check('lowercase hex', S = LowerCase(S), S);

  Check('parse accepts own output', ParseUuid(S, V) and (FormatUuid(V) = S), S);
  Check('parse rejects short input', not ParseUuid('not-a-uuid', V), '');
  Check('parse rejects bad hex', not ParseUuid('{xxxxxxxx-xxxx-4xxx-8xxx-xxxxxxxxxxxx}', V), '');

  Code := Capture([], OutText, ErrText);
  Check('default exits zero', Code = 0, IntToStr(Code));
  Check('default prints one uuid', Length(OutText) > 36, OutText);
  Code := Capture(['-n', '3'], OutText, ErrText);
  Check('-n 3 prints three lines', (Code = 0) and (Length(OutText) > 108), OutText);
  Code := Capture(['--help'], OutText, ErrText);
  Check('--help exits zero', (Code = 0) and (Pos('Usage: {{ npm_name }}', OutText) > 0), OutText);
  Code := Capture(['--bogus'], OutText, ErrText);
  Check('--bogus exits two', (Code = 2) and (Pos('unexpected argument', ErrText) > 0), ErrText);
  Code := Capture(['-n', '0'], OutText, ErrText);
  Check('-n 0 exits two', Code = 2, ErrText);

  WriteLn('checks: ', Passed + Failed, ', passed: ', Passed, ', failed: ', Failed);
  if Failed > 0 then Halt(1);
  Halt(0);
end.
