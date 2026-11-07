"""A 2-d kd-tree over integer point pairs: a split divides, never the answer.

Every point is a leaf of decisions: at one level the plane splits on x,
at the next on y, and a point whose coordinate equals the split walks
right, never left. Membership answers what the walk says, a rectangle
walks both sides whenever it crosses a split, and the nearest answer is
the brute-force argmin with the tie given to the smallest point.
"""

from __future__ import annotations

from .points import ensure_point, ensure_rect

Point = tuple[int, int]
Rect = tuple[int, int, int, int]


class TreeError(ValueError):
    """The tree refused an operation the points do not support."""

    __slots__ = ()


def distance(point: Point, query: Point) -> int:
    """The squared distance the nearest answer is ranked by."""
    dx = point[0] - query[0]
    dy = point[1] - query[1]
    return dx * dx + dy * dy


def inside(point: Point, rect: Rect) -> bool:
    """True when the point sits on or inside the rectangle edges."""
    return rect[0] <= point[0] <= rect[2] and rect[1] <= point[1] <= rect[3]


def goes_left(pair: Point, split: Point, axis: int) -> bool:
    """The descent rule: strictly-less goes left, equal goes right."""
    return pair[axis] < split[axis]


class _Node:
    """One split: a point stands here, the plane divides below it."""

    __slots__ = ("left", "point", "right")

    def __init__(self, point: Point) -> None:
        self.point = point
        self.left: _Node | None = None
        self.right: _Node | None = None


class KDTree:
    """Points in, splits walked, answers equal to the scan's."""

    def __init__(self, points: object = None) -> None:
        self._root: _Node | None = None
        self._size = 0
        for point in points or ():
            self.insert(point)

    def insert(self, point: object) -> bool:
        """Store the pair; False when it was already a point."""
        pair = ensure_point(point)
        if self._root is None:
            self._root = _Node(pair)
            self._size += 1
            return True
        node = self._root
        depth = 0
        while True:
            if pair == node.point:
                return False
            axis = depth % 2
            if goes_left(pair, node.point, axis):
                if node.left is None:
                    node.left = _Node(pair)
                    self._size += 1
                    return True
                node = node.left
            else:
                if node.right is None:
                    node.right = _Node(pair)
                    self._size += 1
                    return True
                node = node.right
            depth += 1

    def has(self, point: object) -> bool:
        """True only when the walk lands on the point itself."""
        pair = ensure_point(point)
        return self._find(self._root, pair, 0) is not None

    def range(self, rect: object) -> list[Point]:
        """Every point inside the rectangle, in lexicographic order."""
        box = ensure_rect(rect)
        found: list[Point] = []
        self._range(self._root, box, 0, found)
        return sorted(found)

    def nearest(self, query: object) -> Point | None:
        """The closest point; ties go to the lexicographically smallest."""
        probe = ensure_point(query)
        best = self._search(self._root, probe, 0, None)
        return None if best is None else best[1]

    def walk(self) -> list[Point]:
        """The in-order walk: left, split, right, at every level."""
        found: list[Point] = []
        self._walk(self._root, found)
        return found

    def audit(self) -> list[str]:
        """The points seated on the wrong side; empty means seated."""
        problems: list[str] = []
        wide: Rect = (-10**9 - 1, -10**9 - 1, 10**9 + 1, 10**9 + 1)
        self._audit(self._root, 0, wide, problems)
        return problems

    def invariant(self) -> bool:
        """True when every split still divides what it should."""
        return not self.audit()

    def count(self) -> int:
        """The points held."""
        return self._size

    def _find(self, node: _Node | None, pair: Point, depth: int) -> _Node | None:
        while node is not None:
            if pair == node.point:
                return node
            axis = depth % 2
            node = node.left if goes_left(pair, node.point, axis) else node.right
            depth += 1
        return None

    def _range(self, node: _Node | None, box: Rect, depth: int,
               found: list[Point]) -> None:
        if node is None:
            return
        if inside(node.point, box):
            found.append(node.point)
        axis = depth % 2
        split = node.point[axis]
        low, high = (box[0], box[2]) if axis == 0 else (box[1], box[3])
        if low < split:
            self._range(node.left, box, depth + 1, found)
        if high >= split:
            self._range(node.right, box, depth + 1, found)

    def _search(self, node: _Node | None, probe: Point, depth: int,
                best: tuple[tuple[int, int, int], Point] | None):
        if node is None:
            return best
        key = (distance(node.point, probe), node.point[0], node.point[1])
        if best is None or key < best[0]:
            best = (key, node.point)
        axis = depth % 2
        diff = probe[axis] - node.point[axis]
        near, far = (node.left, node.right) if diff < 0 else (node.right, node.left)
        best = self._search(near, probe, depth + 1, best)
        if diff * diff <= best[0][0]:
            best = self._search(far, probe, depth + 1, best)
        return best

    def _walk(self, node: _Node | None, found: list[Point]) -> None:
        if node is None:
            return
        self._walk(node.left, found)
        found.append(node.point)
        self._walk(node.right, found)

    def _audit(self, node: _Node | None, depth: int, box: Rect,
               problems: list[str]) -> None:
        if node is None:
            return
        if not inside(node.point, box):
            problems.append(f"point {node.point!r} sits outside its box")
        axis = depth % 2
        split = node.point[axis]
        if axis == 0:
            self._audit(node.left, depth + 1,
                        (box[0], box[1], split - 1, box[3]), problems)
            self._audit(node.right, depth + 1,
                        (split, box[1], box[2], box[3]), problems)
        else:
            self._audit(node.left, depth + 1,
                        (box[0], box[1], box[2], split - 1), problems)
            self._audit(node.right, depth + 1,
                        (box[0], split, box[2], box[3]), problems)

    def __len__(self) -> int:
        return self._size

    def __iter__(self):
        return iter(sorted(self.walk()))
