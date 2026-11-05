function [st, out, ok] = parse_string(raw, st)
%PARSE_STRING Decode a JSON string into its UTF-8 bytes.
  ok = false;
  out = uint8([]);
  if st.pos > st.n || raw(st.pos) ~= 34
    return;
  end
  st.pos = st.pos + 1;
  while true
    if st.pos > st.n
      return;
    end
    c = raw(st.pos);
    if c == 34
      st.pos = st.pos + 1;
      ok = true;
      return;
    elseif c == 92
      st.pos = st.pos + 1;
      if st.pos > st.n
        return;
      end
      e = raw(st.pos);
      st.pos = st.pos + 1;
      if e == 34
        out(end + 1) = 34;
      elseif e == 92
        out(end + 1) = 92;
      elseif e == 47
        out(end + 1) = 47;
      elseif e == 98
        out(end + 1) = 8;
      elseif e == 102
        out(end + 1) = 12;
      elseif e == 110
        out(end + 1) = 10;
      elseif e == 114
        out(end + 1) = 13;
      elseif e == 116
        out(end + 1) = 9;
      elseif e == 117
        [cp, st, ok] = read_hex4(raw, st);
        if ~ok
          return;
        end
        if cp >= 55296 && cp <= 56319
          if st.pos + 1 > st.n || raw(st.pos) ~= 92 || raw(st.pos + 1) ~= 117
            return;
          end
          st.pos = st.pos + 2;
          [low, st, ok] = read_hex4(raw, st);
          if ~ok || low < 56320 || low > 57343
            ok = false;
            return;
          end
          cp = 65536 + (cp - 55296) * 1024 + (low - 56320);
        elseif cp >= 56320 && cp <= 57343
          return;
        end
        out = [out, utf8_of_codepoint(cp)];
      else
        return;
      end
    elseif c < 32
      return;
    else
      out(end + 1) = c;
      st.pos = st.pos + 1;
    end
  end
end

function [value, st, ok] = read_hex4(raw, st)
  value = 0;
  ok = false;
  if st.pos + 3 > st.n
    return;
  end
  for k = 0:3
    d = hex_digit(raw(st.pos + k));
    if d < 0
      return;
    end
    value = value * 16 + d;
  end
  st.pos = st.pos + 4;
  ok = true;
end
