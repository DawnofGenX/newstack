function out = json_quote(bytes)
%JSON_QUOTE Quote raw bytes as a JSON string, escaping only what JSON requires.
  hex = '0123456789ABCDEF';
  out = uint8('"');
  for i = 1:numel(bytes)
    c = bytes(i);
    if c == 34
      out = [out, uint8('\"')];
    elseif c == 92
      out = [out, uint8('\\')];
    elseif c == 10
      out = [out, uint8('\n')];
    elseif c == 13
      out = [out, uint8('\r')];
    elseif c == 9
      out = [out, uint8('\t')];
    elseif c == 8
      out = [out, uint8('\b')];
    elseif c == 12
      out = [out, uint8('\f')];
    elseif c < 32
      out = [out, uint8('\u00'), uint8(hex(floor(c / 16) + 1)), uint8(hex(mod(c, 16) + 1))];
    else
      out(end + 1) = c;
    end
  end
  out(end + 1) = 34;
end
