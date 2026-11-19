% Dependency-free Octave test harness for imghist.
root = fileparts(fileparts(mfilename('fullpath')));
addpath(fullfile(root, '+imghist'));

passed = 0;
failed = 0;
function check(name, cond)
  global passed failed;
  if cond
    passed = passed + 1;
  else
    fprintf('FAIL %s\n', name);
    failed = failed + 1;
  end
end

fixture = sprintf('P2\n3 2\n255\n0 10 20\n20 10 0\n');
img = imghist.parse(fixture);
check('header width', img.width == 3);
check('header height', img.height == 2);
check('pixel count', numel(img.pixels) == 6);
check('pixel values', isequal(img.pixels, [0 10 20 20 10 0]));

counts = imghist.histogram(img.pixels, 4);
check('histogram total', sum(counts) == 6);
check('histogram buckets', isequal(counts, [2 0 2 2]));

s = imghist.summary(img.pixels, counts);
check('summary mean', abs(s.mean - 10) < 1e-9);
check('summary distinct', s.distinct == 3);
check('summary entropy', abs(s.entropy - log2(3)) < 1e-9);

mapped = imghist.equalize(img.pixels);
check('equalize monotone', all(diff(mapped(1:3)) >= 0));
check('equalize range', all(mapped >= 0) && all(mapped <= 20));

bad = false;
try
  imghist.parse('P9\n1 1\n255\n0\n');
catch e
  bad = ~isempty(strfind(e.message, 'unsupported magic'));
end
check('bad magic refused', bad);

outText = '';
errText = '';
emit = @(s) assignin('base', 'outText', [outText s]);
gripe = @(s) assignin('base', 'errText', [errText s]);
readFixture = @(p) fixture;

code = imghist.runner({'--help'}, emit, gripe, readFixture);
check('help exit zero', code == 0);
code = imghist.runner({'--bogus'}, emit, gripe, readFixture);
check('usage error exits two', code == 2);
code = imghist.runner({'--bins'}, emit, gripe, readFixture);
check('missing bins value exits two', code == 2);
code = imghist.runner({'missing.pgm'}, emit, @(s) 1, @(p) error('no file'));
check('missing file exits one', code == 1);
code = imghist.runner({'--json', 'a.pgm'}, emit, gripe, readFixture);
check('json mode succeeds', code == 0);
code = imghist.runner({'--csv', 'a.pgm'}, emit, gripe, readFixture);
check('csv mode succeeds', code == 0);
code = imghist.runner({'--bins', '4', 'a.pgm'}, emit, gripe, readFixture);
check('bins flag succeeds', code == 0);

fprintf('checks: %d, passed: %d, failed: %d\n', passed + failed, passed, failed);
if failed > 0
  exit(1);
end
exit(0);
