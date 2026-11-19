unit uuidopts;
{$mode objfpc}{$H+}
interface
type
  TOptions = record
    Count: Integer;
    Status: Integer;
    Message: string;
  end;
function ParseOptions(const Args: array of string): TOptions;
const
  StatusOk = 0; StatusHelp = 1; StatusUsage = 2;
implementation
uses SysUtils;
function ParseOptions(const Args: array of string): TOptions;
var I: Integer;
begin
  Result.Count := 1;
  Result.Status := StatusOk;
  Result.Message := '';
  I := 0;
  while I < Length(Args) do
  begin
    if (Args[I] = '-h') or (Args[I] = '--help') then
    begin
      Result.Status := StatusHelp;
      Exit;
    end
    else if Args[I] = '-n' then
    begin
      if I + 1 >= Length(Args) then
      begin
        Result.Status := StatusUsage;
        Result.Message := '-n needs a count';
        Exit;
      end;
      try
        Result.Count := StrToInt(Args[I + 1]);
      except
        Result.Status := StatusUsage;
        Result.Message := '-n needs an integer';
        Exit;
      end;
      if (Result.Count < 1) or (Result.Count > 100) then
      begin
        Result.Status := StatusUsage;
        Result.Message := 'count must be between 1 and 100';
        Exit;
      end;
      Inc(I, 2);
    end
    else
    begin
      Result.Status := StatusUsage;
      Result.Message := 'unexpected argument: ' + Args[I];
      Exit;
    end;
  end;
end;
end.
