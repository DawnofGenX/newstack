unit uuidgen;
{$mode objfpc}{$H+}
interface
type
  TUuid = array[0..15] of Byte;
function NewUuidV4: TUuid;
function ParseUuid(const S: string; out U: TUuid): Boolean;
function FormatUuid(const U: TUuid): string;
function Variant(const U: TUuid): Integer;
function Version(const U: TUuid): Integer;
implementation
uses SysUtils;

const HexChars = '0123456789abcdef';

function Nibble(C: Char; out V: Byte): Boolean;
begin
  V := 0;
  Result := False;
  if (C >= '0') and (C <= '9') then V := Ord(C) - Ord('0')
  else if (C >= 'a') and (C <= 'f') then V := Ord(C) - Ord('a') + 10
  else if (C >= 'A') and (C <= 'F') then V := Ord(C) - Ord('A') + 10
  else Exit;
  Result := True;
end;

function NewUuidV4: TUuid;
var I: Integer;
begin
  RandSeed := LongWord(GetTickCount64);
  for I := 0 to 15 do Result[I] := Random(256);
  Result[6] := (Result[6] and $0F) or $40;
  Result[8] := (Result[8] and $3F) or $80;
end;

function ParseUuid(const S: string; out U: TUuid): Boolean;
var I, P: Integer; Hi, Lo: Byte;
begin
  Result := False;
  if Length(S) <> 36 then Exit;
  for I := 0 to 15 do U[I] := 0;
  P := 1;
  for I := 0 to 15 do
  begin
    if (I = 4) or (I = 6) or (I = 8) or (I = 10) then
    begin
      if S[P] <> '-' then Exit;
      Inc(P);
    end;
    if not Nibble(S[P], Hi) then Exit;
    Inc(P);
    if not Nibble(S[P], Lo) then Exit;
    Inc(P);
    U[I] := (Hi shl 4) or Lo;
  end;
  Result := P = 37;
end;

function FormatUuid(const U: TUuid): string;
var I: Integer;
begin
  Result := '';
  for I := 0 to 15 do
  begin
    if (I = 4) or (I = 6) or (I = 8) or (I = 10) then Result := Result + '-';
    Result := Result + HexChars[(U[I] shr 4) + 1] + HexChars[(U[I] and $0F) + 1];
  end;
end;

function Variant(const U: TUuid): Integer;
begin
  Result := (U[8] shr 6) and $03;
end;

function Version(const U: TUuid): Integer;
begin
  Result := (U[6] shr 4) and $0F;
end;
end.
