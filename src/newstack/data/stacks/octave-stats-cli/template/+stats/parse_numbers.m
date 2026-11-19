function nums = parse_numbers(text)
  if isnumeric(text)
    text = char(text);
  end
  tokens = strsplit(strtrim(text));
  vals = [];
  for i = 1:numel(tokens)
    t = tokens{i};
    if isempty(t)
      continue;
    end
    v = str2double(t);
    if ~isnan(v)
      vals(end+1) = v;
    end
  end
  nums = vals;
end
