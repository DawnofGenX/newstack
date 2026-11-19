function out = equalize(pixels)
  % Histogram equalisation: map each pixel through the normalised CDF.
  if isempty(pixels)
    out = pixels;
    return;
  end
  top = max(pixels);
  counts = imghist.histogram(pixels, double(top) + 1);
  cdf = cumsum(counts) / numel(pixels);
  out = arrayfun(@(v) round(cdf(v + 1) * top), pixels);
end
