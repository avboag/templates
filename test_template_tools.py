from __future__ import annotations

import pickle
from dataclasses import dataclass
import sys

if "template_tools" in sys.modules:
    del sys.modules["template_tools"]

from template_tools import Template, parent, parent_method
from typing import Any, ClassVar


@dataclass
class A(Template):
    x: ClassVar[str] = "default"

    y: int

    def __repr__(self):
        return f"{self.x} {self.y}"

    def __eq__(self, other: Any) -> bool:
        if parent(self) != parent(other):
            return NotImplemented
        return self.y == other.y

    def __hash__(self):
        return hash((self.parent, self.y))


class B(A):
    z: ClassVar[int]

    def __init__(self, y: int, t: str):
        super().__init__(y)
        self.t = t

    @parent_method
    @property
    def x(prnt) -> str:  # type: ignore
        return str(prnt.z)

    @parent_method
    def add(self, other: type[B]):
        return B[self.z + other.z]

    def __repr__(self):
        return f"{self.x} {self.y} {self.z} {self.t}"

    def _parent__repr__(prnt):
        return f"B of {prnt.z}"


if __name__ == "__main__":
    assert pickle.loads(pickle.dumps(A)) == A
    assert pickle.loads(pickle.dumps(A["a"])) == A["a"]
    assert pickle.loads(pickle.dumps(A["b"](5))) == A["b"](5)

    assert pickle.loads(pickle.dumps(B)) == B
    assert pickle.loads(pickle.dumps(B[3])) == B[3]
    assert pickle.loads(pickle.dumps(B[4](5, "X"))) == B[4](5, "X")

    assert B[3].add(B[4]) == B[7]

    assert B[3](6, "Y").x == "3"
    assert B[3].x == "3"
