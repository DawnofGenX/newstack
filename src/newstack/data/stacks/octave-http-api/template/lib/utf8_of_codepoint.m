function out = utf8_of_codepoint(cp)
  if cp < 128
    out = uint8(cp);
  elseif cp < 2048
    out = uint8([192 + floor(cp / 64), 128 + mod(cp, 64)]);
  elseif cp < 65536
    out = uint8([224 + floor(cp / 4096), 128 + mod(floor(cp / 64), 64), 128 + mod(cp, 64)]);
  else
    out = uint8([240 + floor(cp / 262144), 128 + mod(floor(cp / 4096), 64), ...
                 128 + mod(floor(cp / 64), 64), 128 + mod(cp, 64)]);
  end
end
