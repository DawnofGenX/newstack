# frozen_string_literal: true

# English pluralisation driven by ordered rules, with irregulars and
# uncountables. Every method is pure: no state, no I/O.
module Pluralize
  # Words that do not change at all.
  UNCOUNTABLE = %w[
    advice aircraft bison cod deer equipment fish furniture gold information
    jeans money moose offspring rice salmon series sheep species staff swine
    trout tuna wheat
  ].freeze

  # singular => plural for words the suffix rules get wrong.
  IRREGULAR = {
    'person' => 'people',
    'man' => 'men',
    'woman' => 'women',
    'child' => 'children',
    'tooth' => 'teeth',
    'foot' => 'feet',
    'goose' => 'geese',
    'mouse' => 'mice',
    'louse' => 'lice',
    'ox' => 'oxen',
    'datum' => 'data',
    'criterion' => 'criteria',
    'phenomenon' => 'phenomena',
    'analysis' => 'analyses',
    'basis' => 'bases',
    'crisis' => 'crises',
    'thesis' => 'theses',
    'index' => 'indices',
    'matrix' => 'matrices',
    'vertex' => 'vertices',
    'appendix' => 'appendices',
    'cactus' => 'cacti',
    'fungus' => 'fungi',
    'nucleus' => 'nuclei',
    'syllabus' => 'syllabi',
    'quiz' => 'quizzes',
    'knife' => 'knives',
    'wife' => 'wives',
    'life' => 'lives',
    'leaf' => 'leaves',
    'half' => 'halves',
    'shelf' => 'shelves',
    'wolf' => 'wolves',
    'calf' => 'calves',
    'loaf' => 'loaves',
    'thief' => 'thieves',
    'potato' => 'potatoes',
    'tomato' => 'tomatoes',
    'hero' => 'heroes',
    'echo' => 'echoes',
    'volcano' => 'volcanoes'
  }.freeze

  # Singular words that already end in "s"; stripping it would mangle them.
  SINGULAR_KEEP = %w[
    atlas bonus bus campus canvas census chaos class compass ethics gas lens
    mathematics news physics politics process status virus
  ].freeze

  PLURAL_OF = IRREGULAR.to_h { |singular, plural| [plural, singular] }.freeze

  # Ordered suffix rules: applied in this order, the first match wins.
  PLURAL_RULES = [
    [/(quiz)$/i, '\1zes'],
    [/([^aeiou])y$/i, '\1ies'],
    [/(s|x|z|ch|sh)$/i, '\1es'],
    [/([^f])fe$/i, '\1ves'],
    [/sis$/i, 'ses'],
    [/$/, 's']
  ].freeze

  SINGULAR_RULES = [
    [/(quizzes)$/i, 'quiz'],
    [/([^aeiou])ies$/i, '\1y'],
    [/(ives)$/i, 'ife'],
    [/ves$/i, 'f'],
    [/([^aeiou])oes$/i, '\1o'],
    [/(sses|shes|ches|xes|zes)$/i, ->(match) { match.sub(/es$/, '') }],
    [/([^s])s$/i, '\1'],
    [/$/, '']
  ].freeze

  module_function

  def plural(word)
    return word if word.empty?
    return word if uncountable?(word)
    lower = word.downcase
    return IRREGULAR[lower] if IRREGULAR.key?(lower)

    apply(PLURAL_RULES, word)
  end

  def singular(word)
    return word if word.empty?
    return word if uncountable?(word)
    lower = word.downcase
    return PLURAL_OF[lower] if PLURAL_OF.key?(lower)
    return word if SINGULAR_KEEP.include?(lower)

    apply(SINGULAR_RULES, word)
  end

  # "1 cat", "2 cats"; the word may arrive in either number.
  def pluralize(count, word)
    number = Integer(count)
    base = singular(word)
    "#{number} #{number.abs == 1 ? base : plural(base)}"
  end

  def uncountable?(word)
    UNCOUNTABLE.include?(word.downcase)
  end

  def apply(rules, word)
    rules.each do |pattern, replacement|
      next unless word.match?(pattern)

      return replacement.respond_to?(:call) ? word.sub(pattern, &replacement) : word.sub(pattern, replacement)
    end
    word
  end
  private_class_method :apply
end
