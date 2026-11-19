module stats
  implicit none
contains

  real function stats_mean(x, n)
    integer, intent(in) :: n
    real, intent(in) :: x(n)
    stats_mean = sum(x) / real(n)
  end function stats_mean

  real function stats_median(x, n)
    integer, intent(in) :: n
    real, intent(in) :: x(n)
    real :: work(n)
    integer :: i, j
    real :: tmp
    work = x
    ! simple insertion sort
    do i = 2, n
      tmp = work(i)
      j = i - 1
      do while (j >= 1 .and. work(j) > tmp)
        work(j+1) = work(j)
        j = j - 1
      end do
      work(j+1) = tmp
    end do
    if (mod(n,2) == 1) then
      stats_median = work((n+1)/2)
    else
      stats_median = (work(n/2) + work(n/2+1)) / 2.0
    end if
  end function stats_median

  real function stats_stdev(x, n)
    integer, intent(in) :: n
    real, intent(in) :: x(n)
    real :: m, acc
    integer :: i
    if (n < 2) then
      stats_stdev = 0.0
      return
    end if
    m = stats_mean(x, n)
    acc = 0.0
    do i = 1, n
      acc = acc + (x(i) - m)**2
    end do
    stats_stdev = sqrt(acc / real(n-1))
  end function stats_stdev

end module stats