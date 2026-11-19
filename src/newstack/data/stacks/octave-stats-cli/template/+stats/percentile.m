function q = percentile(x, p)
  x = sort(x(:));
  n = numel(x);
  if n == 0
    q = NaN;
    return;
  end
  if n == 1
    q = x(1);
    return;
  end
  h = (n - 1) * p + 1;
  lo = floor(h);
  hi = ceil(h);
  if lo < 1, lo = 1; end
  if hi > n, hi = n; end
  q = x(lo) + (h - lo) * (x(hi) - x(lo));
end
