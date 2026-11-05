Counting
========

:func:`{{ package_name }}.count_text` follows ``wc``: a line is a newline, a word is a run
of non-whitespace, and bytes are UTF-8 bytes rather than characters.

Basic counts
------------

.. doctest::

   >>> count_text("hello world\n")
   Counts(lines=1, words=2, bytes=12)
   >>> count_text("")
   Counts(lines=0, words=0, bytes=0)
   >>> count_text("abc")
   Counts(lines=0, words=1, bytes=3)

Bytes are not characters
------------------------

This distinction is why the function returns three numbers instead of one. The next
document is 12 characters and 14 bytes, and a counter that reports 12 is wrong:

.. doctest::

   >>> count_text("héllo wörld\n")
   Counts(lines=1, words=2, bytes=14)

Whitespace that is neither a line nor a word
--------------------------------------------

Tabs and spaces are bytes, but they are not words, and a line needs a newline:

.. doctest::

   >>> count_text("  \t ")
   Counts(lines=0, words=0, bytes=4)

Non-strings are rejected
------------------------

Passing something else is a programming error, not a value to coerce:

.. doctest::

   >>> count_text(42)
   Traceback (most recent call last):
       ...
   TypeError: count_text expects a string, got int
