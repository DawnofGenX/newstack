module root_find
  !! Dependency-free bisection with a checked bracket and an explicit
  !! iteration budget. The function is injected, so the solver is testable
  !! without any command-line or I/O machinery.
  implicit none
  private
  public :: bisect, bracket_error
  abstract interface
    pure function real_function(x) result(y)
      implicit none
      real(8), intent(in) :: x
      real(8) :: y
    end function real_function
  end interface
  type :: bracket_error
    character(len=128) :: message = ''
  end type bracket_error
contains
  subroutine bisect(f, a, b, tol, max_iter, root, iterations, err)
    procedure(real_function) :: f
    real(8), intent(in) :: a, b, tol
    integer, intent(in) :: max_iter
    real(8), intent(out) :: root
    integer, intent(out) :: iterations
    type(bracket_error), intent(out) :: err
    real(8) :: lo, hi, mid, flo, fhi, fmid
    integer :: i
    lo = a
    hi = b
    flo = f(lo)
    fhi = f(hi)
    iterations = 0
    root = 0.0d0
    if (tol <= 0.0d0) then
      err%message = 'tolerance must be positive'
      return
    end if
    if (max_iter < 1) then
      err%message = 'iteration budget must be positive'
      return
    end if
    if (flo == 0.0d0) then
      root = lo
      return
    end if
    if (fhi == 0.0d0) then
      root = hi
      return
    end if
    if ((flo > 0.0d0 .and. fhi > 0.0d0) .or. (flo < 0.0d0 .and. fhi < 0.0d0)) then
      write (err%message, '(A,F0.6,A,F0.6,A)') 'endpoints do not bracket a root: f(', a, ')=', flo
      return
    end if
    do i = 1, max_iter
      iterations = i
      mid = lo + (hi - lo) / 2.0d0
      fmid = f(mid)
      if (fmid == 0.0d0) then
        root = mid
        return
      end if
      if ((flo < 0.0d0) .eqv. (fmid < 0.0d0)) then
        lo = mid
        flo = fmid
      else
        hi = mid
        fhi = fmid
      end if
      root = lo + (hi - lo) / 2.0d0
      if ((hi - lo) / 2.0d0 <= tol) return
    end do
    err%message = 'iteration budget exhausted'
  end subroutine bisect
end module root_find
