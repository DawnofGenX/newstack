unit textstat_counts;
{$mode objfpc}{$H+}
{ Byte-exact counting: the part of the program that has to agree with wc. }

interface

type
  TCounts = record
    Lines: Int64;
    Words: Int64;
    Bytes: Int64;
  end;

  TFigure = (figLines, figWords, figBytes);
  TFigures = set of TFigure;
  TStringArray = array of string;
  TRawBytes = array of Byte;

const
  AllFigures: TFigures = [figLines, figWords, figBytes];

function EmptyCounts: TCounts;
function IsSpaceByte(b: Byte): Boolean;
function CountBytes(const data: TRawBytes): TCounts;
function AddCounts(const a, b: TCounts): TCounts;
function FigureValue(figure: TFigure; const c: TCounts): Int64;

implementation

function EmptyCounts: TCounts;
begin
  Result.Lines := 0;
  Result.Words := 0;
  Result.Bytes := 0;
end;

{ wc uses isspace(3): space, tab, newline, vertical tab, form feed, carriage return. }
function IsSpaceByte(b: Byte): Boolean;
begin
  Result := (b = 32) or (b = 9) or (b = 10) or (b = 13) or (b = 11) or (b = 12);
end;

function CountBytes(const data: TRawBytes): TCounts;
var
  i: SizeInt;
  inWord: Boolean;
begin
  Result := EmptyCounts;
  Result.Bytes := Length(data);
  inWord := False;
  for i := 0 to High(data) do
  begin
    if data[i] = 10 then
    begin
      Inc(Result.Lines);
      inWord := False;
    end
    else if IsSpaceByte(data[i]) then
      inWord := False
    else if not inWord then
    begin
      Inc(Result.Words);
      inWord := True;
    end;
  end;
end;

function AddCounts(const a, b: TCounts): TCounts;
begin
  Result.Lines := a.Lines + b.Lines;
  Result.Words := a.Words + b.Words;
  Result.Bytes := a.Bytes + b.Bytes;
end;

function FigureValue(figure: TFigure; const c: TCounts): Int64;
begin
  case figure of
    figLines: Result := c.Lines;
    figWords: Result := c.Words;
    figBytes: Result := c.Bytes;
  end;
end;

end.
