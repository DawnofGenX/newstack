1;  % script
function [nums, ok] = read_file(path)
  nums = [];
  ok = false;
  fid = fopen(path, 'r');
  if fid < 0
    return;
  end
  raw = fread(fid, Inf, '*char')';
  fclose(fid);
  nums = stats.parse_numbers(raw);
  ok = true;
end

function text = read_stdin()
  text = fread(0, Inf, '*char')';
end

args = argv();
if numel(args) >= 1 && (strcmp(args{1}, '--help') || strcmp(args{1}, '-h'))
  printf('Usage: %s [FILE]\nCompute summary statistics for numbers.\n', '{{ npm_name }}');
  exit(0);
end
if numel(args) > 1
  fprintf(2, 'usage: %s [FILE]\n', '{{ npm_name }}');
  exit(2);
end
if numel(args) == 0
  raw = read_stdin();
  path = '-';
else
  path = args{1};
  [nums_file, ok] = read_file(path);
  if ~ok
    fprintf(2, 'error: cannot open ''%s''\n', path);
    exit(1);
  end
  raw = ''; % already parsed
end
if numel(args) == 0
  nums = stats.parse_numbers(raw);
else
  nums = nums_file;
end
if numel(nums) == 0
  fprintf(2, 'error: no numbers found\n');
  exit(1);
end
s = stats.summarize(nums);
printf('n=%d\n', s.n);
printf('min=%g\n', s.min);
printf('q1=%g\n', s.q1);
printf('median=%g\n', s.median);
printf('q3=%g\n', s.q3);
printf('max=%g\n', s.max);
printf('mean=%g\n', s.mean);
printf('iqr=%g\n', s.iqr);
exit(0);
