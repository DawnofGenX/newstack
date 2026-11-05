function [lines, words, nbytes] = counts(raw)
%COUNT_RAW Byte-exact wc semantics over the raw UTF-8 bytes.
  lines = sum(raw == 10);
  nbytes = numel(raw);
  sep = false(1, 256);
  sep([32 9 10 13 11 12] + 1) = true;
  words = 0;
  inword = false;
  for i = 1:nbytes
    if sep(double(raw(i)) + 1)
      inword = false;
    elseif ~inword
      inword = true;
      words = words + 1;
    end
  end
end
