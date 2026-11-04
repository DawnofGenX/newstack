function c = counts(data)
%COUNTS Byte-exact line, word and byte counts.
%   data may be a uint8 row vector or a char row vector.
  if ischar(data)
    data = uint8(data);
  end
  separators = is_separator(data);
  c.lines = sum(data == 10);
  c.words = word_count(separators);
  c.bytes = numel(data);
end

function total = word_count(separators)
  if isempty(separators)
    total = 0;
    return;
  end
  total = sum(~separators(1:end - 1) & separators(2:end));
  if ~separators(end)
    total = total + 1;
  end
end

function flags = is_separator(data)
  flags = data == 32 | data == 9 | data == 10 | data == 13 | data == 11 | data == 12;
end
