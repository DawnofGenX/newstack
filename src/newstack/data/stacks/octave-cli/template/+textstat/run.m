function code = run(args, io)
%RUN Execute a parsed request against an injected environment.
%   io is a struct of function handles: read_file, read_stdin, write_out and
%   write_err. Nothing here touches the real process.
  parsed = textstat.parse_options(args);

  switch parsed.status
    case 'help'
      io.write_out(usage());
      code = 0;
      return;
    case 'version'
      io.write_out(sprintf('%s\n', textstat.tool_version()));
      code = 0;
      return;
    case 'usage-error'
      io.write_err(sprintf('%s: %s\n', textstat.tool_name(), parsed.message));
      io.write_err(sprintf('Try ''%s --help'' for more information.\n', ...
                           textstat.tool_name()));
      code = 2;
      return;
  end

  files = parsed.files;
  if isempty(files)
    files = {'-'};
  end

  figures = figure_list(parsed);
  rows = {};
  total = struct('lines', 0, 'words', 0, 'bytes', 0);
  failed = false;

  for index = 1:numel(files)
    path = files{index};
    if strcmp(path, '-')
      data = io.read_stdin();
      readable = true;
    else
      [data, readable] = io.read_file(path);
    end

    if ~readable
      io.write_err(sprintf('error: cannot open ''%s''\n', path));
      failed = true;
      continue;
    end

    tally = textstat.counts(data);
    rows{end + 1} = struct('tally', tally, 'label', path);
    total = textstat.add_counts(total, tally);
  end

  if numel(files) > 1
    rows{end + 1} = struct('tally', total, 'label', 'total');
  end

  width = row_width(rows, figures);
  for index = 1:numel(rows)
    io.write_out(row_text(rows{index}.tally, figures, width, rows{index}.label));
  end

  if failed
    code = 1;
  else
    code = 0;
  end
end

function text = usage()
  text = sprintf(['Usage: %s [OPTION]... [FILE]...\n' ...
                  'Print line, word and byte counts for each FILE.\n' ...
                  '  -l, --lines   print the line count\n' ...
                  '  -w, --words   print the word count\n' ...
                  '  -c, --bytes   print the byte count\n' ...
                  '  -h, --help    show this help and exit\n' ...
                  '  -V, --version show the version and exit\n'], textstat.tool_name());
end

function figures = figure_list(parsed)
  figures = {};
  if parsed.lines
    figures{end + 1} = 'lines';
  end
  if parsed.words
    figures{end + 1} = 'words';
  end
  if parsed.bytes
    figures{end + 1} = 'bytes';
  end
end

function width = row_width(rows, figures)
  width = 1;
  for row = 1:numel(rows)
    for index = 1:numel(figures)
      width = max(width, numel(sprintf('%d', rows{row}.tally.(figures{index}))));
    end
  end
end

function text = row_text(tally, figures, width, label)
  cells = cell(1, numel(figures));
  for index = 1:numel(figures)
    cells{index} = pad_left(sprintf('%d', tally.(figures{index})), width);
  end
  text = [strjoin(cells, ' ') ' ' label sprintf('\n')];
end

function text = pad_left(value, width)
  text = [repmat(' ', 1, width - numel(value)) value];
end
