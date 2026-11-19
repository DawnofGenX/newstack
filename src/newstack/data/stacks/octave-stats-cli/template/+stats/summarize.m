function s = summarize(nums)
  x = sort(nums(:));
  s.n = numel(x);
  s.min = x(1);
  s.max = x(end);
  s.mean = mean(x);
  s.q1 = stats.percentile(x, 0.25);
  s.median = stats.percentile(x, 0.5);
  s.q3 = stats.percentile(x, 0.75);
  s.iqr = s.q3 - s.q1;
end
