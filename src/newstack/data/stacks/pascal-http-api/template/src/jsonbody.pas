unit jsonbody;
{ Reads the "text" member of a JSON request body.

  Hand-written on purpose: fpjson hands strings back in the system codepage
  (\\u00e9 arrives as ONE latin-1 byte) and turns a surrogate pair into two
  question marks, which would make the byte count wrong and lose the emoji.
  This reader decodes everything into UTF-8 and keeps a number apart from a
  string: {"text": "42"} is a text, {"text": 42} is not. }
{$mode objfpc}{$H+}

interface

type
  TTextKind = (
    tkInvalid, { not JSON at all, or trailing rubbish after the object }
    tkMissing, { valid JSON without a string "text" member }
    tkText     { a string "text" member }
  );

function ReadTextBody(const Body: AnsiString; out Text: AnsiString): TTextKind;

implementation

uses SysUtils;

type
  EJsonError = class(Exception);

  TScanner = record
    Data: AnsiString;
    Pos: Integer;
  end;

  TFound = (fNone, fString, fOther);

var
  Found: TFound;
  Captured: AnsiString;

procedure SkipSpace(var S: TScanner);
begin
  while (S.Pos <= Length(S.Data)) and (S.Data[S.Pos] in [' ', #9, #10, #13]) do
    Inc(S.Pos);
end;

function Look(var S: TScanner): AnsiChar;
begin
  if S.Pos > Length(S.Data) then
    raise EJsonError.Create('unexpected end of input');
  Result := S.Data[S.Pos];
end;

procedure Expect(var S: TScanner; const C: AnsiChar);
begin
  if Look(S) <> C then
    raise EJsonError.Create('expected ' + C);
  Inc(S.Pos);
end;

function CodePointToUtf8(const Code: Integer): AnsiString;
begin
  if Code < $80 then
    Result := AnsiChar(Code)
  else if Code < $800 then
    Result := AnsiChar($C0 or (Code shr 6)) + AnsiChar($80 or (Code and $3F))
  else if Code < $10000 then
    Result := AnsiChar($E0 or (Code shr 12)) + AnsiChar($80 or ((Code shr 6) and $3F))
      + AnsiChar($80 or (Code and $3F))
  else
    Result := AnsiChar($F0 or (Code shr 18)) + AnsiChar($80 or ((Code shr 12) and $3F))
      + AnsiChar($80 or ((Code shr 6) and $3F)) + AnsiChar($80 or (Code and $3F));
end;

function HexDigit(const C: AnsiChar): Integer;
begin
  case C of
    '0'..'9': Result := Ord(C) - Ord('0');
    'a'..'f': Result := Ord(C) - Ord('a') + 10;
    'A'..'F': Result := Ord(C) - Ord('A') + 10;
  else
    raise EJsonError.Create('bad hex digit');
  end;
end;

function ReadHex4(var S: TScanner): Integer;
var
  Index: Integer;
begin
  Result := 0;
  for Index := 1 to 4 do
  begin
    Result := Result * 16 + HexDigit(Look(S));
    Inc(S.Pos);
  end;
end;

function ParseString(var S: TScanner): AnsiString;
var
  C: AnsiChar;
  Code, Low: Integer;
begin
  Result := '';
  Expect(S, '"');
  while True do
  begin
    C := Look(S);
    if C = '"' then
    begin
      Inc(S.Pos);
      Exit;
    end;
    if C = '\' then
    begin
      Inc(S.Pos);
      C := Look(S);
      Inc(S.Pos);
      case C of
        '"': Result := Result + '"';
        '\': Result := Result + '\';
        '/': Result := Result + '/';
        'b': Result := Result + #8;
        'f': Result := Result + #12;
        'n': Result := Result + #10;
        'r': Result := Result + #13;
        't': Result := Result + #9;
        'u':
          begin
            Code := ReadHex4(S);
            if (Code >= $D800) and (Code <= $DBFF) then
            begin
              if (S.Pos + 1 <= Length(S.Data)) and (S.Data[S.Pos] = '\')
                and (S.Data[S.Pos + 1] = 'u') then
              begin
                Inc(S.Pos, 2);
                Low := ReadHex4(S);
                if (Low >= $DC00) and (Low <= $DFFF) then
                  Code := $10000 + ((Code - $D800) shl 10) + (Low - $DC00);
              end;
            end;
            Result := Result + CodePointToUtf8(Code);
          end;
      else
        raise EJsonError.Create('bad escape');
      end;
    end
    else
    begin
      { A raw byte: UTF-8 payload passes straight through. }
      Result := Result + C;
      Inc(S.Pos);
    end;
  end;
end;

function ParseNumber(var S: TScanner): AnsiString;
begin
  Result := '';
  if (S.Pos <= Length(S.Data)) and (S.Data[S.Pos] = '-') then
  begin
    Result := '-';
    Inc(S.Pos);
  end;
  if S.Pos > Length(S.Data) then
    raise EJsonError.Create('truncated number');
  if not (S.Data[S.Pos] in ['0'..'9']) then
    raise EJsonError.Create('expected a digit');
  while (S.Pos <= Length(S.Data)) and (S.Data[S.Pos] in ['0'..'9']) do
  begin
    Result := Result + S.Data[S.Pos];
    Inc(S.Pos);
  end;
  if (S.Pos <= Length(S.Data)) and (S.Data[S.Pos] in ['.', 'e', 'E', '+', '-']) then
  begin
    { The fractional and exponent parts only need to be scanned: the value is
      never used, only its presence as a non-text member matters. }
    while (S.Pos <= Length(S.Data)) and (S.Data[S.Pos] in ['0'..'9', '.', 'e', 'E', '+', '-']) do
    begin
      Result := Result + S.Data[S.Pos];
      Inc(S.Pos);
    end;
  end;
end;

procedure ParseValue(var S: TScanner; const Depth: Integer); forward;

procedure ParseObject(var S: TScanner; const Depth: Integer);
var
  Key: AnsiString;
begin
  Expect(S, '{');
  SkipSpace(S);
  if Look(S) = '}' then
  begin
    Inc(S.Pos);
    Exit;
  end;
  while True do
  begin
    SkipSpace(S);
    Key := ParseString(S);
    SkipSpace(S);
    Expect(S, ':');
    SkipSpace(S);
    if (Depth = 1) and (Key = 'text') then
    begin
      if Look(S) = '"' then
      begin
        Captured := ParseString(S);
        Found := fString;
      end
      else
      begin
        ParseValue(S, Depth + 1);
        if Found = fNone then
          Found := fOther;
      end;
    end
    else
      ParseValue(S, Depth + 1);
    SkipSpace(S);
    if Look(S) = ',' then
    begin
      Inc(S.Pos);
      Continue;
    end;
    Expect(S, '}');
    Exit;
  end;
end;

procedure ParseArray(var S: TScanner; const Depth: Integer);
begin
  Expect(S, '[');
  SkipSpace(S);
  if Look(S) = ']' then
  begin
    Inc(S.Pos);
    Exit;
  end;
  while True do
  begin
    SkipSpace(S);
    ParseValue(S, Depth + 1);
    SkipSpace(S);
    if Look(S) = ',' then
    begin
      Inc(S.Pos);
      Continue;
    end;
    Expect(S, ']');
    Exit;
  end;
end;

procedure ParseLiteral(var S: TScanner; const Word: AnsiString);
begin
  if Copy(S.Data, S.Pos, Length(Word)) <> Word then
    raise EJsonError.Create('expected ' + Word);
  Inc(S.Pos, Length(Word));
end;

procedure ParseValue(var S: TScanner; const Depth: Integer);
var
  C: AnsiChar;
begin
  C := Look(S);
  case C of
    '{': ParseObject(S, Depth);
    '[': ParseArray(S, Depth);
    '"': ParseString(S);
    't': ParseLiteral(S, 'true');
    'f': ParseLiteral(S, 'false');
    'n': ParseLiteral(S, 'null');
  else
    ParseNumber(S);
  end;
end;

function ReadTextBody(const Body: AnsiString; out Text: AnsiString): TTextKind;
var
  S: TScanner;
begin
  Text := '';
  Captured := '';
  Found := fNone;
  S.Data := Body;
  S.Pos := 1;
  try
    SkipSpace(S);
    if Look(S) <> '{' then
      Exit(tkInvalid);
    ParseObject(S, 1);
    SkipSpace(S);
    if S.Pos <= Length(S.Data) then
      Exit(tkInvalid); { trailing rubbish }
  except
    on EJsonError do
      Exit(tkInvalid);
  end;
  Text := Captured;
  if Found = fString then
    Result := tkText
  else
    Result := tkMissing;
end;

end.
