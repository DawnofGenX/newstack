unit uuidrunner;
{$mode objfpc}{$H+}
interface
uses Classes;
function Run(const Args: array of string; OutStream, ErrStream: TStream): Integer;
implementation
uses SysUtils, uuidgen, uuidopts;
procedure WriteLn(Stream: TStream; const S: string);
var Line: string;
begin
  Line := S + LineEnding;
  Stream.WriteBuffer(Line[1], Length(Line));
end;
function Run(const Args: array of string; OutStream, ErrStream: TStream): Integer;
var Opts: TOptions; U: TUuid; I: Integer;
begin
  Opts := ParseOptions(Args);
  case Opts.Status of
    uuidopts.StatusHelp:
      begin
        WriteLn(OutStream, 'Generate RFC 4122 version 4 UUIDs.');
        WriteLn(OutStream, 'Usage: {{ npm_name }} [-n COUNT]');
        Result := 0;
        Exit;
      end;
    uuidopts.StatusUsage:
      begin
        WriteLn(ErrStream, '{{ npm_name }}: ' + Opts.Message);
        Result := 2;
        Exit;
      end;
  end;
  for I := 1 to Opts.Count do
  begin
    U := NewUuidV4;
    WriteLn(OutStream, FormatUuid(U));
  end;
  Result := 0;
end;
end.
