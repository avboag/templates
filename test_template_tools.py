from __future__ import annotations

import pickle
from dataclasses import dataclass

from template_tools import template, ParentParent


@template
class A:
    @classmethod
    def _parent(cls, x: str = 'default'):
        return locals()

    def __init__(self, y):
        self.y = y

    def __repr__(self):
        return f"{self.parent.x} {self.y}"

    def __eq__(self, other):
        if not isinstance(other, A):
            return NotImplemented
        return self.parent == other.parent and self.y == other.y

    def __hash__(self):
        return hash((self.parent, self.y))


@dataclass(frozen=True)
class CustomBParent(ParentParent):
    x: int

    @property
    def z(self):
        return self.x + "_but_good"

    def __add__(self, other):
        if isinstance(other, CustomBParent):
            return B._parent(self.x + "_" + other.x)
        return NotImplemented


@template
class B:
    @classmethod
    def _parent(cls, x: str = 'default'):
        return CustomBParent(cls, x)

    def __init__(self, y):
        self.y = y

    def __repr__(self):
        return f"{self.parent.x} {self.y}"

    def __eq__(self, other):
        if not isinstance(other, B):
            return NotImplemented
        return self.parent == other.parent and self.y == other.y

    def __hash__(self):
        return hash((self.parent, self.y))


if __name__ == '__main__':
    assert pickle.loads(pickle.dumps(A)) == A
    assert pickle.loads(pickle.dumps(A('a'))) == A('a')
    assert pickle.loads(pickle.dumps(A('b')(5))) == A('b')(5)

    assert pickle.loads(pickle.dumps(B)) == B
    assert pickle.loads(pickle.dumps(B('a'))) == B('a')
    assert pickle.loads(pickle.dumps(B('b')(5))) == B('b')(5)

    assert B('a') + B('b') == B('a_b')
