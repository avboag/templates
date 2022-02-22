from __future__ import annotations

__all__ = 'template', 'ParentParent'

from dataclasses import dataclass
import pickle
from functools import cache


@dataclass(frozen=True, slots=True)
class ParentParent:
    cl: type

    def __call__(self, *args, **kwargs):
        res = object.__new__(self.cl)
        res.parent = self
        res.__init__(*args, **kwargs)

        return res
        # The reason we don't do this:
        # return self.cl(*args, _parent=self, **kwargs)
        # is that then _parent would get passed to the __init__
        # in addition to the proper arguments.
        # We could wrap __init__ to accomodate this, but
        # profiling showed the wrapping takes a significant performance
        # overhead, and this is the more efficient solution.

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


def template_new(cls, *args, _real=False, **kwargs):
    """
    If _real=False, create the appropriate parent.
    If _real=True, create a clean object of this class.
    Note that this object cannot be used directly as it has no
    parent. This option is provided solely for pickle.
    """

    if _real:
        return object.__new__(cls)

    return template_new_parent_creator(cls, *args, **kwargs)


TEMPLATE_NEW_UNPICKLE_ARGS = ((), {'_real': True})


def template_getnewargs_ex(self=None):
    return TEMPLATE_NEW_UNPICKLE_ARGS


def template(cl):
    cl.__new__ = template_new
    cl.__getnewargs_ex__ = template_getnewargs_ex

    return cl
