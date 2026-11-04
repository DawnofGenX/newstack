function total = add_counts(left, right)
%ADD_COUNTS Sum two count structures.
  total.lines = left.lines + right.lines;
  total.words = left.words + right.words;
  total.bytes = left.bytes + right.bytes;
end
