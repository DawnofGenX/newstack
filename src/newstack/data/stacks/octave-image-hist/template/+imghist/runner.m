
function code = runner(args, out, err, read_file)
  % CLI core with injected output, error and file reader; tests call it directly.
  bins = 256;
  mode = 'text';
  path = '';
  i = 1;
  while i <= numel(args)
    a = args{i};
    if strcmp(a, '--help')
      out("Usage: {{ npm_name }} [--bins N] [--json|--csv] [--equalize] PGM\n");
      code = 0;
      return;
    elseif strcmp(a, '--json')
      mode = 'json';
    elseif strcmp(a, '--csv')
      mode = 'csv';
    elseif strcmp(a, '--equalize')
      mode = 'equalize';
    elseif strcmp(a, '--bins')
      i = i + 1;
      if i > numel(args)
        err("error: --bins needs a value\n");
        code = 2;
        return;
      end
      bins = str2double(args{i});
      if isnan(bins) || bins < 1 || fix(bins) ~= bins
        err("error: --bins must be a positive integer\n");
        code = 2;
        return;
      end
    elseif strcmp(a(1), '-')
      err(sprintf('error: unknown option %s\n', a));
      code = 2;
      return;
    else
      path = a;
    end
    i = i + 1;
  end
  if isempty(path)
    err("error: expected a PGM file\n");
    code = 2;
    return;
  end
  try
    text = read_file(path);
    img = imghist.parse(text);
  catch e
    err(sprintf('error: %s\n', e.message));
    code = 1;
    return;
  end
  counts = imghist.histogram(img.pixels, bins);
  s = imghist.summary(img.pixels, counts);
  if strcmp(mode, 'json')
    out(sprintf('{"n":%d,"mean":%.4f,"min":%d,"max":%d,"entropy":%.4f,"distinct":%d}\n', ...
        s.n, s.mean, s.min, s.max, s.entropy, s.distinct));
  elseif strcmp(mode, 'csv')
    for k = 1:numel(counts)
      out(sprintf('%d,%d\n', k - 1, counts(k)));
    end
  elseif strcmp(mode, 'equalize')
    mapped = imghist.equalize(img.pixels);
    out(sprintf('%s\n', strjoin(arrayfun(@(v) num2str(v), mapped, ...
        'UniformOutput', false), ' ')));
  else
    out(sprintf('image: %dx%d maxval=%d\n', img.width, img.height, img.maxval));
    out(sprintf('n=%d mean=%.4f min=%d max=%d distinct=%d entropy=%.4f\n', ...
        s.n, s.mean, s.min, s.max, s.distinct, s.entropy));
    [topCounts, topIdx] = sort(counts, 'descend');
    for k = 1:min(3, numel(topCounts))
      if topCounts(k) > 0
        out(sprintf('bin %d: %d\n', topIdx(k) - 1, topCounts(k)));
      end
    end
  end
  code = 0;
end
