"""A string-keyed trie over lowercase words: a word ends where it is whole.

Every word is a path of single-letter branches from the root, and the
word lives at the node its last letter reaches -- no word hides inside
a longer one, no branch stands open on a word nobody stored. Membership
answers what the path says, a prefix listing walks the open branches
under a stem in lexicographic order, and a delete closes exactly the
one node the word names and prunes only the branches that fall silent.
"""

from __future__ import annotations

from .words import ensure_prefix, ensure_word


class TrieError(ValueError):
    """The trie refused an operation the words do not support."""

    __slots__ = ()


class _Node:
    """One branch point: a letter arrived, a word may end here."""

    __slots__ = ("children", "terminal")

    def __init__(self) -> None:
        self.children: dict[str, _Node] = {}
        self.terminal = False

    def branch(self) -> bool:
        """True when this node or any node below it holds a word."""
        return self.terminal or any(child.branch() for child in self.children.values())


class PrefixTrie:
    """Words in, letters walked, answers in lexicographic order."""

    def __init__(self, words: object = None) -> None:
        self._root = _Node()

        self._size = 0
        for word in words or ():
            self.insert(word)

    def insert(self, word: str) -> bool:
        """Store the whole word; False when it was already a word."""
        node = self._root
        for letter in ensure_word(word):
            node = node.children.setdefault(letter, _Node())
        if node.terminal:
            return False
        node.terminal = True
        self._size += 1
        return True

    def has(self, word: str) -> bool:
        """True only when the walk lands on the node the word ends at."""
        ensure_word(word)
        node = self._walk(word)
        return node is not None and node.terminal

    def delete(self, word: str) -> bool:
        """Close the word's own node; prune only branches gone silent."""
        ensure_word(word)
        path: list[tuple[_Node, str]] = []
        node = self._root
        for letter in word:
            child = node.children.get(letter)
            if child is None:
                return False
            path.append((node, letter))
            node = child
        if not node.terminal:
            return False
        node.terminal = False
        self._size -= 1
        for parent, letter in reversed(path):
            if parent.children[letter].branch():
                break
            del parent.children[letter]
        return True

    def prefix(self, stem: str = "") -> list[str]:
        """Every word under the stem, in lexicographic order."""
        ensure_prefix(stem)
        node = self._walk(stem)
        if node is None:
            return []
        found: list[str] = []
        self._collect(node, stem, found)
        return found

    def longest_common_prefix(self) -> str:
        """The stem every held word shares; empty when they share none."""
        words = self.walk()
        if not words:
            return ""
        head = words[0]
        for word in words[1:]:
            limit = min(len(head), len(word))
            stop = 0
            while stop < limit and head[stop] == word[stop]:
                stop += 1
            head = head[:stop]
            if not head:
                break
        return head

    def walk(self) -> list[str]:
        """Every word, in lexicographic order."""
        return self.prefix("")

    def audit(self) -> list[str]:
        """The dangling branches a delete left open; empty means seated."""
        problems: list[str] = []
        self._audit(self._root, "", problems)
        return problems

    def invariant(self) -> bool:
        """True when no branch stands open on a word nobody stores."""
        return not self.audit()

    def count(self) -> int:
        """The words held."""
        return self._size

    def _walk(self, word: str) -> _Node | None:
        node = self._root
        for letter in word:
            node = node.children.get(letter)
            if node is None:
                return None
        return node

    def _collect(self, node: _Node, stem: str, found: list[str]) -> None:
        if node.terminal:
            found.append(stem)
        for letter in sorted(node.children):
            self._collect(node.children[letter], stem + letter, found)

    def _audit(self, node: _Node, path: str, problems: list[str]) -> None:
        for letter, child in sorted(node.children.items()):
            if not child.branch():
                problems.append(f"dangling branch at {path + letter!r}")
            self._audit(child, path + letter, problems)

    def __len__(self) -> int:
        return self._size

    def __iter__(self):
        return iter(self.walk())
