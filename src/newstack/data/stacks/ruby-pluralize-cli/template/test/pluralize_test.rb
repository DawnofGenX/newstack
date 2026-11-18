# frozen_string_literal: true

require 'minitest/autorun'
require 'pluralize'

class PluralizeTest < Minitest::Test
  def test_regular_suffixes
    {
      'cat' => 'cats',
      'dog' => 'dogs',
      'bus' => 'buses',
      'box' => 'boxes',
      'church' => 'churches',
      'dish' => 'dishes',
      'quiz' => 'quizzes',
      'city' => 'cities',
      'day' => 'days',
      'photo' => 'photos',
      'potato' => 'potatoes',
      'hero' => 'heroes',
      'knife' => 'knives',
      'roof' => 'roofs',
      'analysis' => 'analyses'
    }.each do |singular, plural|
      assert_equal plural, Pluralize.plural(singular), singular
    end
  end

  def test_irregulars
    {
      'person' => 'people',
      'child' => 'children',
      'man' => 'men',
      'woman' => 'women',
      'tooth' => 'teeth',
      'foot' => 'feet',
      'mouse' => 'mice',
      'ox' => 'oxen',
      'datum' => 'data',
      'criterion' => 'criteria',
      'index' => 'indices'
    }.each do |singular, plural|
      assert_equal plural, Pluralize.plural(singular), singular
    end
  end

  def test_uncountables_never_change
    %w[sheep fish deer series species equipment information money].each do |word|
      assert_equal word, Pluralize.plural(word)
      assert_equal word, Pluralize.singular(word)
    end
  end

  def test_singular_reverses_plural
    %w[cat box city knife analysis person child tooth sheep potato hero].each do |singular|
      assert_equal singular, Pluralize.singular(Pluralize.plural(singular)), singular
    end
  end

  def test_singular_handles_already_singular_words
    %w[cat dog bus status].each do |word|
      assert_equal word, Pluralize.singular(word)
    end
  end

  def test_count_uses_the_singular_for_one
    assert_equal '1 cat', Pluralize.pluralize(1, 'cat')
    assert_equal '1 child', Pluralize.pluralize(1, 'children')
    assert_equal '0 cats', Pluralize.pluralize(0, 'cats')
    assert_equal '3 people', Pluralize.pluralize(3, 'person')
    assert_equal '1 sheep', Pluralize.pluralize(1, 'sheep')
  end
end
