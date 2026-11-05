module {{ class_name }}
  record Counts, lines : Int32, words : Int32, bytes : Int32

  # A line is a newline byte, a word is a maximal run of non-space bytes and
  # `bytes` is the UTF-8 byte size (Crystal's `size` counts characters).
  def self.count_text(text : String) : Counts
    Counts.new(
      lines: text.count('\n').to_i32,
      words: text.scan(/\S+/).size.to_i32,
      bytes: text.bytesize.to_i32,
    )
  end
end
