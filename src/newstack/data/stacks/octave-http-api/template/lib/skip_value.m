function [st, ok] = skip_value(raw, st, depth)
%SKIP_VALUE Walk one JSON value without keeping it.
  ok = false;
  if depth > 32 || st.pos > st.n
    return;
  end
  c = raw(st.pos);
  if c == 34
    [st, ~, ok] = parse_string(raw, st);
    return;
  elseif c == 123
    st.pos = st.pos + 1;
    [st, ok] = skipws(raw, st);
    if ~ok
      return;
    end
    if st.pos <= st.n && raw(st.pos) == 125
      st.pos = st.pos + 1;
      ok = true;
      return;
    end
    while true
      [st, ~, ok] = parse_string(raw, st);
      if ~ok
        return;
      end
      [st, ok] = skipws(raw, st);
      if ~ok || st.pos > st.n || raw(st.pos) ~= 58
        return;
      end
      st.pos = st.pos + 1;
      [st, ok] = skipws(raw, st);
      if ~ok
        return;
      end
      [st, ok] = skip_value(raw, st, depth + 1);
      if ~ok
        return;
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
        ok = true;
        return;
      else
        return;
      end
    end
  elseif c == 91
    st.pos = st.pos + 1;
    [st, ok] = skipws(raw, st);
    if ~ok
      return;
    end
    if st.pos <= st.n && raw(st.pos) == 93
      st.pos = st.pos + 1;
      ok = true;
      return;
    end
    while true
      [st, ok] = skip_value(raw, st, depth + 1);
      if ~ok
        return;
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
      elseif raw(st.pos) == 93
        st.pos = st.pos + 1;
        ok = true;
        return;
      else
        return;
      end
    end
  elseif c == 45 || (c >= 48 && c <= 57)
    if c == 45
      st.pos = st.pos + 1;
    end
    [st, ok] = scan_number(raw, st);
    return;
  elseif starts_with(raw, st, 'true')
    st.pos = st.pos + 4;
    ok = true;
    return;
  elseif starts_with(raw, st, 'false')
    st.pos = st.pos + 5;
    ok = true;
    return;
  elseif starts_with(raw, st, 'null')
    st.pos = st.pos + 4;
    ok = true;
    return;
  end
end

function [st, ok] = scan_number(raw, st)
  ok = false;
  start = st.pos;
  if st.pos <= st.n && raw(st.pos) == 48
    st.pos = st.pos + 1;
  else
    while st.pos <= st.n && raw(st.pos) >= 48 && raw(st.pos) <= 57
      st.pos = st.pos + 1;
    end
  end
  if st.pos <= st.n && raw(st.pos) == 46
    st.pos = st.pos + 1;
    while st.pos <= st.n && raw(st.pos) >= 48 && raw(st.pos) <= 57
      st.pos = st.pos + 1;
    end
  end
  if st.pos <= st.n && (raw(st.pos) == 101 || raw(st.pos) == 69)
    st.pos = st.pos + 1;
    if st.pos <= st.n && (raw(st.pos) == 43 || raw(st.pos) == 45)
      st.pos = st.pos + 1;
    end
    while st.pos <= st.n && raw(st.pos) >= 48 && raw(st.pos) <= 57
      st.pos = st.pos + 1;
    end
  end
  ok = st.pos > start;
end

function yes = starts_with(raw, st, word)
  n = numel(word);
  yes = false;
  if st.pos + n - 1 > st.n
    return;
  end
  yes = isequal(char(raw(st.pos:st.pos + n - 1)), word);
end
