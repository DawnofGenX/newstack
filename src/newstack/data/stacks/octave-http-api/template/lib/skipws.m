function [st, ok] = skipws(raw, st)
  ok = true;
  while st.pos <= st.n
    c = raw(st.pos);
    if c == 32 || c == 9 || c == 10 || c == 13
      st.pos = st.pos + 1;
    else
      return;
    end
  end
end
