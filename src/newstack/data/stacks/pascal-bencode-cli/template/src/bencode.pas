unit bencode;
{$mode objfpc}{$H+}
interface
type
  TBencodeType = (btInt, btStr, btList, btDict);
  PBencode = ^TBencode;
  TBencode = record
    typ: TBencodeType;
    intVal: Int64;
    strVal: AnsiString;
    items: array of PBencode;
    keys: array of AnsiString;
    vals: array of PBencode;
  end;

function NewInt(v: Int64): PBencode;
function NewStr(const v: AnsiString): PBencode;
function NewList: PBencode;
function NewDict: PBencode;
procedure ListAppend(l, v: PBencode);
procedure DictSet(d: PBencode; const key: AnsiString; v: PBencode);
function Encode(v: PBencode): AnsiString;
function Decode(const s: AnsiString; out v: PBencode): Boolean;

implementation

uses SysUtils;

function NewInt(v: Int64): PBencode;
begin
  New(Result);
  Result^.typ := btInt;
  Result^.intVal := v;
  Result^.strVal := '';
end;

function NewStr(const v: AnsiString): PBencode;
begin
  New(Result);
  Result^.typ := btStr;
  Result^.strVal := v;
end;

function NewList: PBencode;
begin
  New(Result);
  Result^.typ := btList;
end;

function NewDict: PBencode;
begin
  New(Result);
  Result^.typ := btDict;
end;

procedure ListAppend(l, v: PBencode);
begin
  SetLength(l^.items, Length(l^.items) + 1);
  l^.items[High(l^.items)] := v;
end;

procedure DictSet(d: PBencode; const key: AnsiString; v: PBencode);
var
  i: Integer;
begin
  for i := 0 to High(d^.keys) do
    if d^.keys[i] = key then
    begin
      d^.vals[i] := v;
      Exit;
    end;
  SetLength(d^.keys, Length(d^.keys) + 1);
  SetLength(d^.vals, Length(d^.vals) + 1);
  d^.keys[High(d^.keys)] := key;
  d^.vals[High(d^.vals)] := v;
end;

function Encode(v: PBencode): AnsiString;
var
  i, j, tmp: Integer;
  order: array of Integer;
begin
  if v = nil then
  begin
    Result := '';
    Exit;
  end;
  case v^.typ of
    btInt: Result := 'i' + IntToStr(v^.intVal) + 'e';
    btStr: Result := IntToStr(Length(v^.strVal)) + ':' + v^.strVal;
    btList:
      begin
        Result := 'l';
        for i := 0 to High(v^.items) do
          Result := Result + Encode(v^.items[i]);
        Result := Result + 'e';
      end;
    btDict:
      begin
        SetLength(order, Length(v^.keys));
        for i := 0 to High(order) do
          order[i] := i;
        for i := 1 to High(order) do
        begin
          j := i;
          while (j > 0) and (v^.keys[order[j-1]] > v^.keys[order[j]]) do
          begin
            tmp := order[j];
            order[j] := order[j-1];
            order[j-1] := tmp;
            Dec(j);
          end;
        end;
        Result := 'd';
        for i := 0 to High(order) do
        begin
          Result := Result + IntToStr(Length(v^.keys[order[i]])) + ':' + v^.keys[order[i]] + Encode(v^.vals[order[i]]);
        end;
        Result := Result + 'e';
      end;
  end;
end;

function ParseInt(const s: AnsiString; var i: SizeInt; out value: Int64): Boolean;
var
  neg: Boolean;
begin
  Result := False;
  value := 0;
  neg := False;
  if i > Length(s) then Exit;
  if s[i] = '-' then
  begin
    neg := True;
    Inc(i);
  end;
  if i > Length(s) then Exit;
  if (s[i] < '0') or (s[i] > '9') then Exit;
  while (i <= Length(s)) and (s[i] >= '0') and (s[i] <= '9') do
  begin
    value := value * 10 + (Ord(s[i]) - Ord('0'));
    Inc(i);
  end;
  if i > Length(s) then Exit;
  if s[i] <> 'e' then Exit;
  Inc(i);
  if neg then value := -value;
  Result := True;
end;

function ParseStr(const s: AnsiString; var i: SizeInt; out value: AnsiString): Boolean;
var
  len: Int64;
  j: SizeInt;
begin
  Result := False;
  value := '';
  len := 0;
  if i > Length(s) then Exit;
  if (s[i] < '0') or (s[i] > '9') then Exit;
  while (i <= Length(s)) and (s[i] >= '0') and (s[i] <= '9') do
  begin
    len := len * 10 + (Ord(s[i]) - Ord('0'));
    Inc(i);
  end;
  if i > Length(s) then Exit;
  if s[i] <> ':' then Exit;
  Inc(i);
  if i + len - 1 > Length(s) then Exit;
  SetLength(value, len);
  for j := 0 to len - 1 do
    value[j+1] := s[i + j];
  Inc(i, len);
  Result := True;
end;

function ParseValue(const s: AnsiString; var i: SizeInt; out v: PBencode): Boolean;
var
  iv: Int64;
  sv: AnsiString;
  tmp: PBencode;
begin
  Result := False;
  v := nil;
  if i > Length(s) then Exit;
  case s[i] of
    'i':
      begin
        Inc(i);
        if not ParseInt(s, i, iv) then Exit;
        v := NewInt(iv);
        Result := True;
      end;
    'l':
      begin
        Inc(i);
        v := NewList;
        while (i <= Length(s)) and (s[i] <> 'e') do
        begin
          if not ParseValue(s, i, tmp) then Exit;
          ListAppend(v, tmp);
        end;
        if i > Length(s) then Exit;
        if s[i] <> 'e' then Exit;
        Inc(i);
        Result := True;
      end;
    'd':
      begin
        Inc(i);
        v := NewDict;
        while (i <= Length(s)) and (s[i] <> 'e') do
        begin
          if not ParseStr(s, i, sv) then Exit;
          if not ParseValue(s, i, tmp) then Exit;
          DictSet(v, sv, tmp);
        end;
        if i > Length(s) then Exit;
        if s[i] <> 'e' then Exit;
        Inc(i);
        Result := True;
      end;
    '0'..'9':
      begin
        if not ParseStr(s, i, sv) then Exit;
        v := NewStr(sv);
        Result := True;
      end;
  end;
end;

function Decode(const s: AnsiString; out v: PBencode): Boolean;
var
  i: SizeInt;
begin
  i := 1;
  Result := ParseValue(s, i, v);
  if not Result then Exit;
  if i <= Length(s) then
  begin
    Result := False;
    v := nil;
  end;
end;

end.
