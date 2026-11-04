program {{ package_name }};
{$mode objfpc}{$H+}
{ The only file that touches the real process: open, read, write, exit. }

uses BaseUnix, SysUtils, textstat_counts, textstat_options, textstat_runner;

function ReadAll(fd: cint): TRawBytes;
var
  buffer: array[0..65535] of Byte;
  n: TSsize;
  total: SizeInt;
begin
  Result := nil;
  total := 0;
  repeat
    n := fpRead(fd, buffer, SizeOf(buffer));
    if n > 0 then
    begin
      if total + n > Length(Result) then
        SetLength(Result, total + n + 65536);
      Move(buffer, Result[total], n);
      Inc(total, n);
    end;
  until n <= 0;
  SetLength(Result, total);
end;

function ReadPath(const path_: string; out ok: Boolean): TRawBytes;
var
  fd: cint;
begin
  ok := False;
  Result := nil;
  if path_ = '-' then
  begin
    Result := ReadAll(0);
    ok := True;
    Exit;
  end;
  fd := fpOpen(path_, O_RDONLY);
  if fd < 0 then
    Exit;
  Result := ReadAll(fd);
  fpClose(fd);
  ok := True;
end;

procedure WriteStdout(const text: string);
begin
  Write(text);
  Flush(Output);
end;

procedure WriteStderr(const text: string);
begin
  Write(StdErr, text);
  Flush(StdErr);
end;

var
  args: TStringArray;
  io: TIo;
  i: Integer;
begin
  SetLength(args, ParamCount);
  for i := 1 to ParamCount do
    args[i - 1] := ParamStr(i);
  io.ReadFile := @ReadPath;
  io.WriteOut := @WriteStdout;
  io.WriteErr := @WriteStderr;
  ExitCode := Run(args, io);
end.
