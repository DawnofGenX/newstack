function [kind, text] = jsonread(raw)
%JSONREAD Keep only the `text` member of a JSON object.
% past a closing brace; the last `text` member wins.
  kind = 'invalid';
  text = uint8([]);
  st = struct('pos', 1, 'n', numel(raw));
  [st, ok] = skipws(raw, st);
  if ~ok || st.pos > st.n || raw(st.pos) ~= 123
    return;
  end
  st.pos = st.pos + 1;
  found = false;
  [st, ok] = skipws(raw, st);
  if ~ok
    return;
  end
  if st.pos <= st.n && raw(st.pos) == 125
    st.pos = st.pos + 1;
  else
    while true
      [st, key, ok] = parse_string(raw, st);
      if ~ok
        return;
      end
      [st, ok] = skipws(raw, st);
      if ~ok || st.pos > st.n || raw(st.pos) ~= 58
        return;
      end
      st.pos = st.pos + 1;
      [st, ok] = skipws(raw, st);
      if ~ok || st.pos > st.n
        return;
      end
      if isequal(char(key), 'text')
        if raw(st.pos) ~= 34
          return;
        end
        [st, text, ok] = parse_string(raw, st);
        if ~ok
          return;
        end
        found = true;
      else
        [st, ok] = skip_value(raw, st, 0);
        if ~ok
          return;
        end
      end
      [st, ok] = skipws(raw, st);
      if ~ok || st.pos > st.n
        return;
      end
      if raw(st.pos) == 44
        st.pos = st.pos + 1;
        [st, ok] = skipws(raw, st);
        if ~ok
          return;
        end
      elseif raw(st.pos) == 125
        st.pos = st.pos + 1;
        break;
      else
        return;
      end
    end
  end
  [st, ok] = skipws(raw, st);
  if ~ok || st.pos <= st.n
    return;
  end
  if found
    kind = 'text';
  else
    kind = 'missing';
    text = uint8([]);
  end
end
