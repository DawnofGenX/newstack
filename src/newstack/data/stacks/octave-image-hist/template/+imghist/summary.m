function s = summary(pixels, counts)
  % Distribution facts that are useful for exposure decisions.
  if isempty(pixels)
    s = struct('n', 0, 'mean', 0, 'min', 0, 'max', 0, 'entropy', 0, ...
               'median', 0, 'distinct', 0);
    return;
  end
  p = double(pixels(:));
  probs = counts / sum(counts);
  probs = probs(probs > 0);
  s = struct('n', numel(p), 'mean', mean(p), 'min', min(p), 'max', max(p), ...
             'entropy', -sum(probs .* log2(probs)), ...
             'median', median(p), 'distinct', numel(unique(p)));
end
