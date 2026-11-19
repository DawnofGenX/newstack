program main;
{$mode objfpc}{$H+}
uses Classes, SysUtils, uuidrunner;
var Args: array of string; I: Integer;
begin
  SetLength(Args, ParamCount);
  for I := 1 to ParamCount do Args[I - 1] := ParamStr(I);
  Halt(Run(Args, THandleStream.Create(StdOutputHandle), THandleStream.Create(StdErrorHandle)));
end.
