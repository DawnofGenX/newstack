# frozen_string_literal: true

require_relative 'test_helper'

class ReportTest < Minitest::Test
  def setup
    @rows = [
      { 'dept' => 'eng', 'salary' => '100', 'name' => 'a' },
      { 'dept' => 'eng', 'salary' => '200', 'name' => 'b' },
      { 'dept' => 'hr', 'salary' => '50', 'name' => 'c' }
    ]
  end

  def test_groups_count
    r = CsvReport::Report.new(@rows, 'dept')
    aggs = r.aggregates
    eng = aggs.find { |a| a['group'] == 'eng' }
    assert_equal 2, eng['count']
    hr = aggs.find { |a| a['group'] == 'hr' }
    assert_equal 1, hr['count']
  end

  def test_numeric_sums
    r = CsvReport::Report.new(@rows, 'dept')
    aggs = r.aggregates
    eng = aggs.find { |a| a['group'] == 'eng' }
    assert_equal 300.0, eng['sum_salary']
    assert_in_delta 150.0, eng['avg_salary'], 0.001
  end

  def test_non_numeric_excluded
    r = CsvReport::Report.new(@rows, 'dept')
    assert_equal ['salary'], r.numeric_columns
  end

  def test_table_and_json
    r = CsvReport::Report.new(@rows, 'dept')
    assert r.to_table.include?('eng')
    json = JSON.parse(r.to_json)
    assert_equal 2, json['groups'].size
  end

  def test_default_group_column
    r = CsvReport::Report.new(@rows)
    assert_equal 'dept', r.group_column
  end
end
