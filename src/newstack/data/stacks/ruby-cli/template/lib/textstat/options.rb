# frozen_string_literal: true

module Textstat
  # Raised for anything the user could have typed correctly; the CLI turns it into
  # a usage line on stderr and exit code 2, which is the shell's "wrong usage".
  class UsageError < StandardError; end

  # Parsed command line. `paths` are untouched: opening them is the CLI's job, so
  # this class stays a pure function of argv and can be tested without a file.
  Options = Data.define(:mode, :help, :version, :paths, :json) do
    def self.parse(argv)
      mode = { lines: true, words: true, bytes: true }
      chosen = []
      help = version = json = false
      paths = []

      argv.each do |arg|
        case arg
        when "--help", "-h" then help = true
        when "--version", "-V" then version = true
        when "--json" then json = true
        when "-l" then chosen << :lines
        when "-w" then chosen << :words
        when "-c" then chosen << :bytes
        when "-" then paths << "-"
        else
          raise UsageError, "unknown option: #{arg}" if arg.start_with?("-") && arg != "-"

          paths << arg
        end
      end

      unless chosen.empty?
        mode = mode.transform_values { false }.merge(chosen.to_h { |key| [key, true] })
      end
      new(mode:, help:, version:, paths:, json:)
    end

    def lines? = mode.fetch(:lines)
    def words? = mode.fetch(:words)
    def bytes? = mode.fetch(:bytes)
  end
end
