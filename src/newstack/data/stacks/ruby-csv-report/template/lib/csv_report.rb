# frozen_string_literal: true

# ruby-csv-report

require 'csv'
require 'json'

module CsvReport
  class Report
    attr_reader :rows, :group_column

    def initialize(rows, group_column = nil)
      @rows = rows
      @group_column = group_column || (rows.empty? ? nil : rows.first.keys.first)
    end

    def groups
      @rows.group_by { |r| r[@group_column] }
    end

    def numeric_columns
      @rows.empty? ? [] : @rows.first.keys.reject { |c| c == @group_column }.select do |col|
        @rows.all? { |r| r[col].to_s.strip.match?(/\A-?\d+(\.\d+)?\z/) }
      end
    end

    def aggregates
      groups.map do |key, items|
        agg = { 'group' => key, 'count' => items.size }
        numeric_columns.each do |col|
          vals = items.map { |r| r[col].to_f }
          agg["sum_#{col}"] = vals.sum
          agg["avg_#{col}"] = vals.empty? ? 0.0 : vals.sum / vals.size
        end
        agg
      end.sort_by { |a| a['group'].to_s }
    end

    def to_table
      aggs = aggregates
      cols = ['group', 'count'] + numeric_columns.flat_map { |c| ["sum_#{c}", "avg_#{c}"] }
      widths = cols.map do |c|
        [c.length, *aggs.map { |a| a[c].to_s.length }].max
      end
      header = cols.each_with_index.map { |c, i| c.ljust(widths[i]) }.join('  ')
      sep = widths.map { |w| '-' * w }.join('  ')
      lines = [header, sep]
      aggs.each do |a|
        lines << cols.each_with_index.map { |c, i| a[c].to_s.ljust(widths[i]) }.join('  ')
      end
      lines.join("\n")
    end

    def to_json
      JSON.generate('groups' => aggregates)
    end
  end

  class CLI
    def initialize(stdin: $stdin, stdout: $stdout, stderr: $stderr)
      @stdin = stdin
      @stdout = stdout
      @stderr = stderr
    end

    def run(argv)
      file = argv[0]
      group = nil
      i = 1
      while i < argv.size
        case argv[i]
        when '--group', '-g'
          group = argv[i + 1]
          i += 2
        else
          i += 1
        end
      end

      unless file && File.exist?(file)
        @stderr.puts "usage: csv-report FILE [--group COLUMN]"
        return 2
      end

      rows = CSV.read(file, headers: true).map(&:to_h)
      report = Report.new(rows, group)
      @stdout.puts report.to_table
      @stdout.puts
      @stdout.puts report.to_json
      0
    end
  end
end
