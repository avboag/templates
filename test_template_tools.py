from __future__ import annotations

import pickle
from dataclasses import dataclass
import sys

if "template_tools" in sys.modules:
    del sys.modules["template_tools"]

from template_tools import Parent, Template, parent, parent_method
from typing import Any, ClassVar


class A(Template):
    x: ClassVar[str] = "default"

    def __init__(self, y):
        self.y = y

    def __repr__(self):
        return f"{self.x} {self.y}"

    def __eq__(self, other):
        if parent(self) != parent(other):
            return NotImplemented
        return self.y == other.y

    def __hash__(self):
        return hash((self.parent, self.y))


class B(A):
    z: ClassVar[int]

    class ParentExtras(Parent):
        def __add__(self, other):
            return B[self.z + other.z]  # type: ignore

    @parent_method
    @property
    def x(prnt):  # type: ignore
        return str(prnt.z)


if __name__ == "__main__":
    assert pickle.loads(pickle.dumps(A)) == A
    assert pickle.loads(pickle.dumps(A["a"])) == A["a"]
    assert pickle.loads(pickle.dumps(A["b"](5))) == A["b"](5)

    assert pickle.loads(pickle.dumps(B)) == B
    assert pickle.loads(pickle.dumps(B[3])) == B[3]
    assert pickle.loads(pickle.dumps(B[4](5))) == B[4](5)

    assert B[3] + B[4] == B[7]

    assert B[3](6).x == "3"
    assert B[3].x == "3"
