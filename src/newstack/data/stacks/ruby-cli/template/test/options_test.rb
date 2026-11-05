# frozen_string_literal: true

require_relative "test_helper"

class OptionsTest < Minitest::Test
  def test_defaults_count_everything_and_read_no_path
    options = Textstat::Options.parse([])
    assert_equal [true, true, true], [options.lines?, options.words?, options.bytes?]
    assert_empty options.paths
    refute options.json
  end

  def test_choosing_one_flag_turns_the_others_off
    options = Textstat::Options.parse(["-c", "file.txt"])
    assert_equal [false, false, true], [options.lines?, options.words?, options.bytes?]
    assert_equal ["file.txt"], options.paths
  end

  def test_flags_can_be_combined_and_repeated
    options = Textstat::Options.parse(["-l", "-c", "-l", "-"])
    assert_equal [true, false, true], [options.lines?, options.words?, options.bytes?]
    assert_equal ["-"], options.paths
  end

  def test_double_dash_still_counts_as_stdin
    assert_equal ["-"], Textstat::Options.parse(["-"]).paths
  end

  def test_an_unknown_option_is_a_usage_error
    error = assert_raises(Textstat::UsageError) { Textstat::Options.parse(["--bogus"]) }
    assert_equal "unknown option: --bogus", error.message
  end

  def test_help_and_version_are_flags_not_paths
    options = Textstat::Options.parse(["--help"])
    assert options.help
    assert_empty options.paths
  end
end
