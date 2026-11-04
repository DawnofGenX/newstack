structure TestMain = struct
  fun main () =
    let
      val () = CountsTest.run ()
      val () = OptionsTest.run ()
      val () = RunnerTest.runTests ()
      val () = Harness.finish ()
    in
      ()
    end
end

val () = TestMain.main ()
