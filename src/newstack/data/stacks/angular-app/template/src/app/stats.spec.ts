import { countText, summarize } from './stats';

describe('countText', () => {
  it('counts nothing in an empty string', () => {
    expect(countText('')).toEqual({ lines: 0, words: 0, bytes: 0 });
  });

  it('counts a single line', () => {
    expect(countText('a b\n')).toEqual({ lines: 1, words: 2, bytes: 4 });
  });

  it('counts several lines and words', () => {
    expect(countText('a b\nc\n')).toEqual({ lines: 2, words: 3, bytes: 6 });
  });

  it('counts bytes, not code units', () => {
    // Two accented letters add three bytes on top of the eleven characters.
    expect(countText('h\u00e9llo w\u00f6rld\n')).toEqual({ lines: 1, words: 2, bytes: 14 });
  });

  it('treats a missing trailing newline as one line', () => {
    expect(countText('a b\nc')).toEqual({ lines: 1, words: 3, bytes: 5 });
  });

  it('counts vertical tab and form feed as separators', () => {
    expect(countText('a\u000bb\u000cc').words).toBe(3);
  });

  it('summarises in singular and plural', () => {
    expect(summarize({ lines: 1, words: 2, bytes: 3 })).toBe('1 line \u00b7 2 words \u00b7 3 bytes');
    expect(summarize({ lines: 0, words: 0, bytes: 0 })).toBe('0 lines \u00b7 0 words \u00b7 0 bytes');
  });
});
