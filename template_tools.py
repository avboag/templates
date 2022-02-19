# from __future__ import annotations

__all__ = 'template', 'ParentParent'

from dataclasses import dataclass
import pickle
from functools import cache


@dataclass(frozen=True, slots=True)
class ParentParent:
    cl: type

    def __call__(self, *args, **kwargs):
        return self.cl(*args, _parent=self, **kwargs)


@dataclass(frozen=True)
class DefaultParent(ParentParent):
    _arguments: list[tuple[str, Any]]

    def __init__(self, cl, arguments):
        ParentParent.__init__(cl)

        object.__setattr__(self, '_arguments', arguments)

        for key, value in self._arguments:
            if key.startswith('_'):
                raise ValueError('Template params cannot begin with an underscore')

            object.__setattr__(self, key, value)

    def __repr__(self):
        binding_repr = ", ".join(
            (f"{value}" if False else f"{name}={value}")
            for name, value in self._arguments
        )

        return f"{self.cl.__name__}({binding_repr})"


@cache
def template_new_parent_creator(cls, *args, **kwargs):
    res = cls._parent(*args, **kwargs)

    if isinstance(res, dict):
        del res['cls']
        res = DefaultParent(cls, list(res.items()))

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


def template_init_creator(init):
    def template_init(self, *args, _parent, **kwargs):
        # assert _parent is not None

        return init(self, *args, **kwargs)

    return template_init


def template(cl):
    cl.__init__ = template_init_creator(cl.__init__)

    cl.__new__ = template_new
    cl.__getnewargs_ex__ = template_getnewargs_ex

    return cl
