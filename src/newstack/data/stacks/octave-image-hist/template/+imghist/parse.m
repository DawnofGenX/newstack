function img = parse(text)
  % Parse a grayscale Netpbm image (P2 ASCII or P5 binary) from text bytes.
  % Returns a struct with width, height, maxval and a pixels row vector.
  % The reader hands us bytes as a char array so the binary form survives.
  if isempty(text) || ~strcmp(text(1:2), 'P2') && ~strcmp(text(1:2), 'P5')
    error('image-hist: unsupported magic (expected P2 or P5)');
  end
  binary = strcmp(text(1:2), 'P5');
  pos = 3;
  tokens = {};
  for k = 1:3
    [tok, pos] = next_token(text, pos);
    tokens{k} = tok;
  end
  width = str2double(tokens{1});
  height = str2double(tokens{2});
  maxval = str2double(tokens{3});
  if isnan(width) || isnan(height) || isnan(maxval) || width < 1 || height < 1 ...
      || maxval < 1 || maxval > 65535
    error('image-hist: invalid image header');
  end
  if pos <= numel(text) && isspace(text(pos))
    pos = pos + 1;
  end
  n = width * height;
  if binary
    if pos + n - 1 > numel(text)
      error('image-hist: truncated pixel data');
    end
    bytes = double(uint8(text(pos:pos+n-1)));
    if maxval > 255
      if pos + 2*n - 1 > numel(text)
        error('image-hist: truncated 16-bit pixel data');
      end
      hi = double(uint8(text(pos:2:pos+2*n-2)));
      lo = double(uint8(text(pos+1:2:pos+2*n-1)));
      bytes = hi * 256 + lo;
    end
    pixels = bytes;
  else
    values = [];
    while numel(values) < n
      [tok, pos] = next_token(text, pos);
      if isempty(tok)
        error('image-hist: truncated pixel data');
      end
      v = str2double(tok);
      if isnan(v) || v < 0 || v > maxval || fix(v) ~= v
        error('image-hist: invalid pixel value');
      end
      values(end+1) = v;
    end
    pixels = values;
  end
  img = struct('width', width, 'height', height, 'maxval', maxval, 'pixels', pixels);
end

function [tok, pos] = next_token(text, pos)
  while pos <= numel(text) && (isspace(text(pos)) || text(pos) == '#')
    if text(pos) == '#'
      while pos <= numel(text) && text(pos) ~= sprintf('\n')
        pos = pos + 1;
      end
    else
      pos = pos + 1;
    end
  end
  start = pos;
  while pos <= numel(text) && ~isspace(text(pos))
    pos = pos + 1;
  end
  tok = text(start:pos-1);
end
