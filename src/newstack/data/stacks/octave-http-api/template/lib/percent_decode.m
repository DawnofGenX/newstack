function out = percent_decode(s)
%PERCENT_DECODE Turn %XX into bytes and '+' into a space.
  s = uint8(s);
  out = uint8([]);
  i = 1;
  while i <= numel(s)
    c = s(i);
    if c == 37 && i + 2 <= numel(s)
      hi = hex_digit(s(i + 1));
      lo = hex_digit(s(i + 2));
      if hi >= 0 && lo >= 0
        out(end + 1) = hi * 16 + lo;
        i = i + 3;
        continue;
      end
    elseif c == 43
      out(end + 1) = 32;
      i = i + 1;
      continue;
    end
    out(end + 1) = c;
    i = i + 1;
  end
end
