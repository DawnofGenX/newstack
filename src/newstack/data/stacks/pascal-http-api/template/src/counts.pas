unit counts;
{ Counts lines, words and bytes the way wc does. }
{$mode objfpc}{$H+}

interface

type
  TCounts = record
    Lines: Integer;
    Words: Integer;
    Bytes: Integer;
  end;

{ A line ends at #10; a word is a maximal run of non-space characters; bytes
  are the bytes of the UTF-8 payload, not the characters. }
function CountText(const Text: AnsiString): TCounts;

implementation

function IsSpace(C: AnsiChar): Boolean;
begin
  Result := (C = ' ') or (C = #9) or (C = #11) or (C = #12) or (C = #13) or (C = #10);
end;

function CountText(const Text: AnsiString): TCounts;
var
  Index: Integer;
  InWord: Boolean;
begin
  Result.Lines := 0;
  Result.Words := 0;
  Result.Bytes := Length(Text);
  InWord := False;
  for Index := 1 to Length(Text) do
  begin
    if Text[Index] = #10 then
      Inc(Result.Lines);
    if IsSpace(Text[Index]) then
      InWord := False
    else
    begin
      if not InWord then
        Inc(Result.Words);
      InWord := True;
    end;
  end;
end;

end.
