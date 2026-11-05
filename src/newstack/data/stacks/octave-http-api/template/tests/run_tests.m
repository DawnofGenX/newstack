% Run the framework-free suite: octave --no-window-system --quiet tests/run_tests.m
here = fileparts(mfilename('fullpath'));
if isempty(here)
  here = pwd;
end
addpath(fullfile(here, '..', 'lib'));
failures = selftest();
if failures > 0
  exit(1);
end
exit(0);
