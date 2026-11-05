unit contract;
{ The whole HTTP contract as one pure function, so it can be tested without a
  socket: health, both stats routes, 422s, 405 and a JSON 404. }
{$mode objfpc}{$H+}

interface

type
  TReply = record
    Status: Integer;
    Body: AnsiString;
  end;

function Route(const Method, Path, Query, Body: AnsiString): TReply;

implementation

uses SysUtils, counts, jsonbody;

function Quote(const Value: AnsiString): AnsiString;
var
  Index: Integer;
  C: AnsiChar;
begin
  Result := '"';
  for Index := 1 to Length(Value) do
  begin
    C := Value[Index];
    case C of
      '"': Result := Result + '\"';
      '\': Result := Result + '\\';
      #10: Result := Result + '\n';
      #13: Result := Result + '\r';
      #9: Result := Result + '\t';
      #8: Result := Result + '\b';
      #12: Result := Result + '\f';
    else
      if C < ' ' then
        Result := Result + '\u' + LowerCase(IntToHex(Ord(C), 4))
      else
        Result := Result + C;
    end;
  end;
  Result := Result + '"';
end;

function CountsJson(const Text: AnsiString; const Totals: TCounts): AnsiString;
begin
  Result := '{"text":' + Quote(Text)
    + ',"lines":' + IntToStr(Totals.Lines)
    + ',"words":' + IntToStr(Totals.Words)
    + ',"bytes":' + IntToStr(Totals.Bytes) + '}';
end;

function Error(const Status: Integer; const Code: AnsiString): TReply;
begin
  Result.Status := Status;
  Result.Body := '{"error":"' + Code + '"}';
end;

function ErrorDetail(const Status: Integer; const Code, Detail: AnsiString): TReply;
begin
  Result.Status := Status;
  Result.Body := '{"error":"' + Code + '","detail":' + Quote(Detail) + '}';
end;

function HexValue(C: AnsiChar): Integer;
begin
  case C of
    '0'..'9': Result := Ord(C) - Ord('0');
    'a'..'f': Result := Ord(C) - Ord('a') + 10;
    'A'..'F': Result := Ord(C) - Ord('A') + 10;
  else
    Result := -1;
  end;
end;

function PercentDecode(const Raw: AnsiString): AnsiString;
var
  Index: Integer;
  High, Low: Integer;
begin
  Result := '';
  Index := 1;
  while Index <= Length(Raw) do
  begin
    if Raw[Index] = '%' then
    begin
      High := HexValue(Raw[Index + 1]);
      Low := HexValue(Raw[Index + 2]);
      if (High >= 0) and (Low >= 0) then
      begin
        Result := Result + AnsiChar(High * 16 + Low);
        Inc(Index, 3);
        Continue;
      end;
    end;
    if Raw[Index] = '+' then
      Result := Result + ' '
    else
      Result := Result + Raw[Index];
    Inc(Index);
  end;
end;

function QueryParam(const Query, Name: AnsiString): AnsiString;
var
  Start, Index, EqualsAt: Integer;
  Pair: AnsiString;
begin
  Result := '';
  Start := 1;
  while Start <= Length(Query) + 1 do
  begin
    Index := Start;
    while (Index <= Length(Query)) and (Query[Index] <> '&') do
      Inc(Index);
    Pair := Copy(Query, Start, Index - Start);
    EqualsAt := Pos('=', Pair);
    if EqualsAt > 0 then
    begin
      if PercentDecode(Copy(Pair, 1, EqualsAt - 1)) = Name then
        Exit(PercentDecode(Copy(Pair, EqualsAt + 1, Length(Pair))));
    end;
    Start := Index + 1;
  end;
end;

function HasQueryParam(const Query, Name: AnsiString): Boolean;
var
  Start, Index, EqualsAt: Integer;
  Pair: AnsiString;
begin
  Result := False;
  Start := 1;
  while Start <= Length(Query) + 1 do
  begin
    Index := Start;
    while (Index <= Length(Query)) and (Query[Index] <> '&') do
      Inc(Index);
    Pair := Copy(Query, Start, Index - Start);
    EqualsAt := Pos('=', Pair);
    if EqualsAt > 0 then
    begin
      if PercentDecode(Copy(Pair, 1, EqualsAt - 1)) = Name then
        Exit(True);
    end;
    Start := Index + 1;
  end;
end;

function Route(const Method, Path, Query, Body: AnsiString): TReply;
var
  Text: AnsiString;
  HasText: Boolean;
begin
  if (Method = 'GET') and (Path = '/health') then
  begin
    Result.Status := 200;
    Result.Body := '{"status":"ok"}';
    Exit;
  end;
  if (Method = 'GET') and (Path = '/stats') then
  begin
    HasText := HasQueryParam(Query, 'text');
    Text := QueryParam(Query, 'text');
    if not HasText then
      Exit(Error(422, 'missing_text'));
    Result.Status := 200;
    Result.Body := CountsJson(Text, CountText(Text));
    Exit;
  end;
  if (Method = 'POST') and (Path = '/stats') then
  begin
    case ReadTextBody(Body, Text) of
      tkInvalid:
        Exit(Error(422, 'invalid_json'));
      tkMissing:
        Exit(Error(422, 'missing_text'));
    end;
    Result.Status := 200;
    Result.Body := CountsJson(Text, CountText(Text));
    Exit;
  end;
  if (Path = '/health') or (Path = '/stats') then
    Exit(Error(405, 'method_not_allowed'));
  Result := ErrorDetail(404, 'not_found', 'no route for ' + Method + ' ' + Path);
end;

end.
