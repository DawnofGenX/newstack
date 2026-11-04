unit textstat_options;
{$mode objfpc}{$H+}
{ argv parsing. The contract is small enough that a hand-written walker beats a unit
  from a package the project would then have to depend on. }

interface

uses textstat_counts, SysUtils;

type
  TStatus = (stOk, stHelp, stVersion, stUsageError);

  TOptions = record
    Status: TStatus;
    Figures: TFigures;
    Files: TStringArray;
    Message: string;
  end;

function ParseOptions(args: TStringArray): TOptions;
function UsageText(const program_: string): string;
function ToolVersion: string;

implementation

const
  ToolVersionString = '0.1.0';

function ToolVersion: string;
begin
  Result := ToolVersionString;
end;

function UsageText(const program_: string): string;
begin
  Result :=
    'Usage: ' + program_ + ' [OPTION]... [FILE]...' + LineEnding +
    'Count lines, words and bytes. With no FILE, or when FILE is -, read standard input.' + LineEnding +
    '  -l, --lines     print the newline count' + LineEnding +
    '  -w, --words     print the word count' + LineEnding +
    '  -c, --bytes     print the byte count' + LineEnding +
    '  -h, --help      print this help' + LineEnding +
    '  -V, --version   print the version' + LineEnding;
end;

procedure Append(var arr: TStringArray; const value: string);
begin
  SetLength(arr, Length(arr) + 1);
  arr[High(arr)] := value;
end;

procedure Remember(var options: TOptions; figure: TFigure);
begin
  Include(options.Figures, figure);
end;

procedure Fail(var options: TOptions; const message: string);
begin
  if options.Status = stOk then
  begin
    options.Status := stUsageError;
    options.Message := message;
  end;
end;

procedure ParseShort(var options: TOptions; const arg: string);
var
  i: Integer;
begin
  for i := 2 to Length(arg) do
    case arg[i] of
      'l': Remember(options, figLines);
      'w': Remember(options, figWords);
      'c': Remember(options, figBytes);
      'h':
        if options.Status = stOk then options.Status := stHelp;
      'V':
        if options.Status = stOk then options.Status := stVersion;
    else
      Fail(options, 'unknown option: -' + arg[i]);
    end;
end;

function ParseOptions(args: TStringArray): TOptions;
var
  i: Integer;
  literal: Boolean;
begin
  Result.Status := stOk;
  Result.Figures := [];
  Result.Files := nil;
  Result.Message := '';
  literal := False;
  for i := 0 to High(args) do
  begin
    if literal then
      Append(Result.Files, args[i])
    else if args[i] = '--' then
      literal := True
    else if (args[i] = '--lines') or (args[i] = '-l') then
      Remember(Result, figLines)
    else if (args[i] = '--words') or (args[i] = '-w') then
      Remember(Result, figWords)
    else if (args[i] = '--bytes') or (args[i] = '-c') then
      Remember(Result, figBytes)
    else if (args[i] = '--help') or (args[i] = '-h') then
    begin
      if Result.Status = stOk then Result.Status := stHelp;
    end
    else if (args[i] = '--version') or (args[i] = '-V') then
    begin
      if Result.Status = stOk then Result.Status := stVersion;
    end
    else if (Length(args[i]) > 2) and (args[i][1] = '-') and (args[i][2] <> '-') then
      ParseShort(Result, args[i])
    else if (Length(args[i]) > 1) and (args[i][1] = '-') and (args[i][2] = '-') then
      Fail(Result, 'unknown option: ' + args[i])
    else
      Append(Result.Files, args[i]);
  end;
  if Result.Figures = [] then
    Result.Figures := AllFigures;
end;

end.
