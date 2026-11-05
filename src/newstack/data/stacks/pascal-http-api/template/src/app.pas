program app;
{$mode objfpc}{$H+}

uses SysUtils, server;

var
  Host: AnsiString;
  Port: Integer;
begin
  Host := AnsiString(GetEnvironmentVariable('HOST'));
  if Host = '' then
    Host := '127.0.0.1';
  Port := StrToIntDef(GetEnvironmentVariable('PORT'), 8080);
  Serve(Host, Port);
end.
