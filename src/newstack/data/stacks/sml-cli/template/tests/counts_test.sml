structure CountsTest = struct
  fun payload text = Byte.stringToBytes text

  fun run () =
    let
      val plain = Counts.count (payload "alpha beta\ngamma\n")
      val () = Harness.equalInt ("two lines", #lines plain, 2)
      val () = Harness.equalInt ("three words", #words plain, 3)
      val () = Harness.equalInt ("bytes are the payload length", #bytes plain, 17)

      val noTrailing = Counts.count (payload "one two three")
      val () = Harness.equalInt ("no trailing newline: lines", #lines noTrailing, 0)
      val () = Harness.equalInt ("no trailing newline: words", #words noTrailing, 3)

      val empty = Counts.count (payload "")
      val () = Harness.equalInt ("empty lines", #lines empty, 0)
      val () = Harness.equalInt ("empty bytes", #bytes empty, 0)

      val spaced = Counts.count (payload "   ")
      val () = Harness.equalInt ("whitespace only has no words", #words spaced, 0)

      val controls = Counts.count (payload "a\tb\011c\012d\n")
      val () = Harness.equalInt ("tab, vtab and form feed separate words", #words controls, 4)

      val sum = Counts.add (plain, noTrailing)
      val () = Harness.equalInt ("add sums lines", #lines sum, 2)
      val () = Harness.equalInt ("add sums words", #words sum, 6)
    in
      ()
    end
end
