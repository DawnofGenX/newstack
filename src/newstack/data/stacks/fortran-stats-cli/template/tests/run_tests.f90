program run_tests
  use stats, only: stats_mean, stats_median, stats_stdev
  use runner, only: run
  implicit none
  integer :: passed=0, failed=0
  real :: x(4) = [1.0,2.0,3.0,4.0]
  integer :: code, u, e, ios
  character(len=256) :: line

  ! mean
  if (abs(stats_mean(x,4)-2.5) < 1e-5) then; passed=passed+1; else; failed=failed+1; print *,'FAIL mean'; endif
  ! median
  if (abs(stats_median(x,4)-2.5) < 1e-5) then; passed=passed+1; else; failed=failed+1; print *,'FAIL median'; endif
  ! stdev sample of 1,2,3,4 = sqrt(5/3)=1.290994
  if (abs(stats_stdev(x,4)-1.290994) < 1e-4) then; passed=passed+1; else; failed=failed+1; print *,'FAIL stdev'; endif

  ! help
  open(newunit=u,file='build/o.txt',status='replace'); open(newunit=e,file='build/er.txt',status='replace')
  code = run([character(len=64)::'--help'], u, e)
  close(u); close(e)
  if (code==0) then; passed=passed+1; else; failed=failed+1; print *,'FAIL help rc'; endif

  ! version
  open(newunit=u,file='build/o.txt',status='replace'); open(newunit=e,file='build/er.txt',status='replace')
  code = run([character(len=64)::'--version'], u, e)
  close(u); close(e)
  if (code==0) then; passed=passed+1; else; failed=failed+1; print *,'FAIL version rc'; endif

  ! unknown
  open(newunit=u,file='build/o.txt',status='replace'); open(newunit=e,file='build/er.txt',status='replace')
  code = run([character(len=64)::'--bogus'], u, e)
  close(u); close(e)
  if (code==2) then; passed=passed+1; else; failed=failed+1; print *,'FAIL usage rc'; endif

  print '(A,I0,A,I0,A,I0)','checks: ',passed+failed,', passed: ',passed,', failed: ',failed
  if (failed>0) call exit(1)
  call exit(0)
end program run_tests