function d = hex_digit(c)
%HEX_DIGIT Value of one hex character, or -1.
  if c >= 48 && c <= 57
    d = double(c) - 48;
  elseif c >= 65 && c <= 70
    d = double(c) - 55;
  elseif c >= 97 && c <= 102
    d = double(c) - 87;
  else
    d = -1;
  end
end
