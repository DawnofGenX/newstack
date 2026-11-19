function counts = histogram(pixels, bins)
  % Count pixels into `bins` equal-width buckets over [0, max(pixels)].
  if nargin < 2
    bins = 256;
  end
  if bins < 1 || bins > 4096
    error('image-hist: bins must be between 1 and 4096');
  end
  if isempty(pixels)
    counts = zeros(1, bins);
    return;
  end
  top = max(pixels);
  edges = linspace(0, top, bins + 1);
  counts = zeros(1, bins);
  for v = pixels
    if v <= 0
      bucket = 1;
    elseif v >= top
      bucket = bins;
    else
      bucket = find(v < edges(2:end), 1);
    end
    counts(bucket) = counts(bucket) + 1;
  end
end
