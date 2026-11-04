unit textstat_runner;
{$mode objfpc}{$H+}
{ The program. Every effect is a parameter, so the suite can drive the whole contract --
  exit codes, total row and error text included -- without spawning a process. }

interface

uses textstat_counts, textstat_options, SysUtils;

type
  TReader = function(const path_: string; out ok: Boolean): TRawBytes;
  TWriter = procedure(const text: string);

  TIo = record
    ReadFile: TReader;
    WriteOut: TWriter;
    WriteErr: TWriter;
  end;

function ProgramName: string;
function Run(args: TStringArray; const io: TIo): Integer;

implementation

const
  ProgramNameValue = '{{ npm_name }}';
  Quote = #39;

function ProgramName: string;
begin
  Result := ProgramNameValue;
end;

function Cell(value: Int64; width: Integer): string;
begin
  Result := IntToStr(value);
  while Length(Result) < width do
    Result := ' ' + Result;
end;

function DigitCount(value: Int64): Integer;
begin
  Result := Length(IntToStr(value));
end;

function RowText(const counts: TCounts; figures: TFigures; const label_: string;
  width: Integer): string;
var
  figure: TFigure;
  printed: Boolean;
begin
  Result := '';
  printed := False;
  for figure := Low(TFigure) to High(TFigure) do
    if figure in figures then
    begin
      if printed then
        Result := Result + ' ';
      Result := Result + Cell(FigureValue(figure, counts), width);
      printed := True;
    end;
  Result := Result + ' ' + label_;
end;

function Run(args: TStringArray; const io: TIo): Integer;
var
  options: TOptions;
  operands: TStringArray;
  labels: TStringArray;
  rows: array of TCounts;
  tally, total: TCounts;
  data: TRawBytes;
  ok, failed: Boolean;
  i, width, digits: Integer;
  figure: TFigure;
  line: string;
begin
  options := ParseOptions(args);
  case options.Status of
    stHelp:
      begin
        io.WriteOut(UsageText(ProgramName));
        Exit(0);
      end;
    stVersion:
      begin
        io.WriteOut(ToolVersion + LineEnding);
        Exit(0);
      end;
    stUsageError:
      begin
        io.WriteErr(ProgramName + ': ' + options.Message + LineEnding);
        io.WriteErr('Try ' + Quote + ProgramName + ' --help' + Quote +
                 ' for more information.' + LineEnding);
        Exit(2);
      end;
  end;

  operands := options.Files;
  if Length(operands) = 0 then
  begin
    SetLength(operands, 1);
    operands[0] := '-';
  end;

  total := EmptyCounts;
  failed := False;
  SetLength(labels, 0);
  SetLength(rows, 0);
  for i := 0 to High(operands) do
  begin
    data := io.ReadFile(operands[i], ok);
    if not ok then
    begin
      failed := True;
      if operands[i] <> '-' then
        io.WriteErr(ProgramName + ': cannot open ' + Quote + operands[i] + Quote + LineEnding);
      Continue;
    end;
    tally := CountBytes(data);
    total := AddCounts(total, tally);
    SetLength(labels, Length(labels) + 1);
    labels[High(labels)] := operands[i];
    SetLength(rows, Length(rows) + 1);
    rows[High(rows)] := tally;
  end;

  if Length(operands) > 1 then
  begin
    SetLength(labels, Length(labels) + 1);
    labels[High(labels)] := 'total';
    SetLength(rows, Length(rows) + 1);
    rows[High(rows)] := total;
  end;

  width := 1;
  for i := 0 to High(rows) do
    for figure := Low(TFigure) to High(TFigure) do
      if figure in options.Figures then
      begin
        digits := DigitCount(FigureValue(figure, rows[i]));
        if digits > width then
          width := digits;
      end;

  for i := 0 to High(rows) do
  begin
    line := RowText(rows[i], options.Figures, labels[i], width);
    io.WriteOut(line + LineEnding);
  end;

  if failed then
    Exit(1)
  else
    Exit(0);
end;

end.
