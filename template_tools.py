from __future__ import annotations

__all__ = 'template', 'ParentParent'

from dataclasses import dataclass
import pickle
from functools import cache


@dataclass(frozen=True, slots=True)
class ParentParent:
    cl: type

    def __call__(self, *args, **kwargs):
        return self.cl(*args, _parent=self, **kwargs)


class DefaultParent(ParentParent):
    def __init__(self, cl, **kwargs):
        ParentParent.__init__(self, cl)

        if any(key.startswith('_') for key in kwargs.keys()):
            raise ValueError('Template params cannot begin with an underscore')

        self.__dict__.update(kwargs)

    def __repr__(self):
        binding_repr = ", ".join(
            (f"{value}" if False else f"{name}={value}")
            for name, value in self.__dict__.items()
        )

        return f"{self.cl.__name__}({binding_repr})"

    def __eq__(self, other):
        if not isinstance(other, DefaultParent):
            return NotImplemented
        return self.cl == other.cl and self.__dict__ == other.__dict__

    def __hash__(self):
        return hash(tuple(self.__dict__.items()))

    def __getstate__(self):
        return self.cl, self.__dict__

    def __setstate__(self, state):
        cl, dct = state

        object.__setattr__(self, 'cl', cl)
        self.__dict__.update(dct)


@cache
def template_new_parent_creator(cls, *args, **kwargs):
    res = cls._parent(*args, **kwargs)

    if isinstance(res, dict):
        del res['cls']
        res = DefaultParent(cls, **res)

    return res


def template_new(cls, *args, _parent=None, **kwargs):
    if _parent is not None:
        res = object.__new__(cls)
        res.parent = _parent

        return res

    return template_new_parent_creator(cls, *args, **kwargs)


TEMPLATE_NEW_UNPICKLE_ARGS = ((), {'_parent': False})


def template_getnewargs_ex(self):
    return TEMPLATE_NEW_UNPICKLE_ARGS


def template(cl):
    init = cl.__init__
    cl.__init__ = lambda *args, _parent, **kwargs: init(*args, **kwargs)

    cl.__new__ = template_new
    cl.__getnewargs_ex__ = template_getnewargs_ex

    return cl
