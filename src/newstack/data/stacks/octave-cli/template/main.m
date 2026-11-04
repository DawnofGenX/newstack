1;  % this is a script, not a function file

function [data, ok] = read_file(path)
  data = uint8([]);
  ok = false;
  handle = fopen(path, 'rb');
  if handle < 0
    return;
  end
  data = fread(handle, Inf, 'uint8')';
  fclose(handle);
  ok = true;
end

function data = read_stdin()
  data = fread(0, Inf, 'uint8')';
end

function write_out(text)
  fputs(1, text);
end

function write_err(text)
  fputs(2, text);
end

% Entry point: the only place that touches the real process.
args = argv();
io.read_file = @read_file;
io.read_stdin = @read_stdin;
io.write_out = @write_out;
io.write_err = @write_err;
exit(textstat.run(args, io));
