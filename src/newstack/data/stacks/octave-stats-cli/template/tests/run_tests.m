1;
PASSED = 0; FAILED = 0;
function check(name, ok)
  global PASSED FAILED;
  if ok, PASSED++; else, FAILED++; printf('FAIL %s\n', name); end
end
function check_equal(name, a, b)
  check(name, isequal(a,b));
end
nums = stats.parse_numbers('1 2 3 4 5');
s = stats.summarize(nums);
check_equal('n', s.n, 5);
check_equal('min', s.min, 1);
check_equal('q1', s.q1, 2);
check_equal('median', s.median, 3);
check_equal('q3', s.q3, 4);
check_equal('max', s.max, 5);
check_equal('iqr', s.iqr, 2);
check_equal('mean', s.mean, 3);
bad = false;
try
  stats.summarize([]);
catch
  bad = true;
end
check('empty raises', bad);
printf('checks: %d, passed: %d, failed: %d\n', PASSED+FAILED, PASSED, FAILED);
if FAILED == 0
  exit(0);
else
  exit(1);
end
