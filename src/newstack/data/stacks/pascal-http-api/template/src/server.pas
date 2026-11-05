unit server;
{ A blocking HTTP/1.1 server on the fcl-web listener, one request at a time. }
{$mode objfpc}{$H+}

interface

procedure Serve(const Host: AnsiString; const Port: Integer);

implementation

uses SysUtils, fphttpserver, contract;

type
  TService = class
  public
    procedure Handle(Sender: TObject; var ARequest: TFPHTTPConnectionRequest;
      var AResponse: TFPHTTPConnectionResponse);
  end;

procedure TService.Handle(Sender: TObject; var ARequest: TFPHTTPConnectionRequest;
  var AResponse: TFPHTTPConnectionResponse);
var
  Reply: TReply;
  Path: AnsiString;
  Cut: Integer;
begin
  Path := AnsiString(ARequest.URI);
  Cut := Pos('?', Path);
  if Cut > 0 then
    Path := Copy(Path, 1, Cut - 1);
  Reply := Route(AnsiString(ARequest.Method), Path, AnsiString(ARequest.Query),
    AnsiString(ARequest.Content));
  AResponse.Code := Reply.Status;
  AResponse.ContentType := 'application/json';
  AResponse.Content := Reply.Body;
end;

procedure Serve(const Host: AnsiString; const Port: Integer);
var
  Http: TFPHTTPServer;
  Service: TService;
begin
  Service := TService.Create;
  Http := TFPHTTPServer.Create(nil);
  try
    Http.Port := Port;
    Http.HostName := Host;
    Http.OnRequest := @Service.Handle;
    Http.Active := True;
    WriteLn('listening on http://', Host, ':', Port);
    while True do
      Sleep(1000);
  finally
    Http.Free;
    Service.Free;
  end;
end;

end.
