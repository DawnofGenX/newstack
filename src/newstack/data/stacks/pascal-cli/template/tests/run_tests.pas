program run_tests;
{$mode objfpc}{$H+}
{ A dependency-free suite: no fpcunit, no lazarus. The runner talks to the world
  through a record of function pointers, so the suite can drive the whole
  contract -- exit codes, total row and error text included. }

uses SysUtils, textstat_counts, textstat_options, textstat_runner;

var
  Passed: Integer = 0;
  Failed: Integer = 0;
  OutBuf: string = '';
  ErrBuf: string = '';
  Fixture: TRawBytes;
  FixturePath: string = 'fixture.txt';

procedure WriteOut(const text: string);
begin
  OutBuf := OutBuf + text;
end;

procedure WriteErr(const text: string);
begin
  ErrBuf := ErrBuf + text;
end;

function ReadFixture(const path_: string; out ok: Boolean): TRawBytes;
begin
  Result := nil;
  ok := (path_ = FixturePath) or (path_ = '-');
  if ok then
    Result := Fixture;
end;

function BytesOf(const text: string): TRawBytes;
var
  i: Integer;
begin
  Result := nil;
  SetLength(Result, Length(text));
  for i := 1 to Length(text) do
    Result[i - 1] := Byte(text[i]);
end;

procedure ResetBuffers;
begin
  OutBuf := '';
  ErrBuf := '';
end;

procedure Check(const name: string; ok: Boolean; const detail: string = '');
begin
  if ok then
    Inc(Passed)
  else
  begin
    Inc(Failed);
    WriteLn('FAIL ', name);
    if detail <> '' then
      WriteLn('     ', detail);
  end;
end;

procedure CheckInt(const name: string; got, want: Int64);
begin
  Check(name, got = want, Format('got %d, want %d', [got, want]));
end;

procedure CheckText(const name, got, want: string);
begin
  Check(name, got = want, Format('got %s, want %s',
    [QuotedStr(got), QuotedStr(want)]));
end;

function RunCapture(const args: TStringArray; const text: string): Integer;
var
  io: TIo;
begin
  Fixture := BytesOf(text);
  ResetBuffers;
  io.ReadFile := @ReadFixture;
  io.WriteOut := @WriteOut;
  io.WriteErr := @WriteErr;
  Result := Run(args, io);
end;

procedure CountsTests;
var
  counts: TCounts;
  data: TRawBytes;
begin
  counts := CountBytes(BytesOf('alpha beta' + #10 + 'gamma delta' + #10));
  CheckInt('plain lines', counts.Lines, 2);
  CheckInt('plain words', counts.Words, 4);
  CheckInt('plain bytes', counts.Bytes, 23);

  counts := CountBytes(BytesOf(''));
  CheckInt('empty lines', counts.Lines, 0);
  CheckInt('empty words', counts.Words, 0);
  CheckInt('empty bytes', counts.Bytes, 0);

  { No trailing newline: wc counts the last partial line as a line. }
  counts := CountBytes(BytesOf('alpha beta' + #10 + 'gamma'));
  CheckInt('no trailing newline lines', counts.Lines, 1);
  CheckInt('no trailing newline words', counts.Words, 3);
  CheckInt('no trailing newline bytes', counts.Bytes, 16);

  { Two bytes of UTF-8: counting has to be on bytes, not characters. }
  data := BytesOf('h' + #$C3 + #$A9 + 'llo' + ' ' + 'w' + #$C3 + #$B6 + 'rld' + #10);
  counts := CountBytes(data);
  CheckInt('utf8 lines', counts.Lines, 1);
  CheckInt('utf8 words', counts.Words, 2);
  CheckInt('utf8 bytes', counts.Bytes, 14);

  { Vertical tab and form feed are separators, so this is four words. }
  counts := CountBytes(BytesOf('a' + #9 + 'b' + #11 + 'c' + #12 + 'd' + #10));
  CheckInt('vertical tab and form feed lines', counts.Lines, 1);
  CheckInt('vertical tab and form feed words', counts.Words, 4);
  CheckInt('vertical tab and form feed bytes', counts.Bytes, 8);

  counts := AddCounts(CountBytes(BytesOf('a b' + #10)), CountBytes(BytesOf('c d e' + #10)));
  CheckInt('added lines', counts.Lines, 2);
  CheckInt('added words', counts.Words, 5);
  CheckInt('added bytes', counts.Bytes, 10);
end;

procedure OptionsTests;
var
  options: TOptions;
begin
  options := ParseOptions(nil);
  Check('default status is ok', options.Status = stOk);
  Check('default shows every figure',
    (figLines in options.Figures) and (figWords in options.Figures) and
    (figBytes in options.Figures));
  CheckInt('default has no files', Length(options.Files), 0);

  options := ParseOptions(['-l']);
  Check('single flag keeps one figure', options.Figures = [figLines]);

  options := ParseOptions(['-lw', 'a.txt', 'b.txt']);
  Check('cluster keeps two figures', options.Figures = [figLines, figWords]);
  CheckInt('cluster keeps both files', Length(options.Files), 2);

  options := ParseOptions(['--bytes', 'a.txt']);
  Check('long flag', options.Figures = [figBytes]);

  options := ParseOptions(['--', '-l']);
  Check('terminator stops flag parsing', options.Files[0] = '-l');
  Check('terminator leaves the default figures',
    options.Figures = [figLines, figWords, figBytes]);

  options := ParseOptions(['-']);
  Check('a lone dash is a file', (Length(options.Files) = 1) and (options.Files[0] = '-'));

  options := ParseOptions(['--help']);
  Check('help status', options.Status = stHelp);

  options := ParseOptions(['-V']);
  Check('version status', options.Status = stVersion);

  options := ParseOptions(['--bogus']);
  Check('unknown option status', options.Status = stUsageError);
  CheckText('unknown option message', options.Message, 'unknown option: --bogus');
end;

procedure RunnerTests;
var
  code: Integer;
  stdio: TIo;
begin
  code := RunCapture([FixturePath], 'alpha beta' + #10 + 'gamma delta' + #10);
  CheckInt('one file exit code', code, 0);
  CheckText('one file row', OutBuf, ' 2  4 23 fixture.txt' + LineEnding);

  code := RunCapture(['-l', FixturePath], 'a' + #10 + 'b' + #10);
  CheckInt('single figure exit code', code, 0);
  CheckText('single figure row', OutBuf, '2 fixture.txt' + LineEnding);

  Fixture := BytesOf('');
  ResetBuffers;
  stdio.ReadFile := @ReadFixture;
  stdio.WriteOut := @WriteOut;
  stdio.WriteErr := @WriteErr;
  code := Run(['-w'], stdio);
  CheckInt('stdin exit code', code, 0);
  CheckText('stdin is labelled with a dash', OutBuf, '0 -' + LineEnding);

  code := RunCapture([FixturePath, 'missing.txt'], 'a b' + #10);
  CheckInt('unreadable file exit code', code, 1);
  Check('unreadable file names the path', Pos('missing.txt', ErrBuf) > 0, ErrBuf);
  CheckText('unreadable file still prints the total row', OutBuf,
    '1 2 4 fixture.txt' + LineEnding + '1 2 4 total' + LineEnding);

  code := RunCapture(['--help'], '');
  CheckInt('help exit code', code, 0);
  Check('help mentions usage', Pos('Usage:', OutBuf) > 0, OutBuf);

  code := RunCapture(['--version'], '');
  CheckInt('version exit code', code, 0);
  CheckText('version text', OutBuf, '0.1.0' + LineEnding);

  code := RunCapture(['--bogus'], '');
  CheckInt('usage error exit code', code, 2);
  Check('usage error names the option', Pos('--bogus', ErrBuf) > 0, ErrBuf);
end;

begin
  CountsTests;
  OptionsTests;
  RunnerTests;
  WriteLn(Format('checks: %d, passed: %d, failed: %d', [Passed + Failed, Passed, Failed]));
  if Failed > 0 then
    ExitCode := 1;
end.
