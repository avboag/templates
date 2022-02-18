from __future__ import annotations

__all__ = 'template', 'ParentParent'

from dataclasses import dataclass
import inspect
import pickle


@dataclass(frozen=True, slots=True)
class ParentParent:
    cl: type

    def __call__(self, *args, **kwargs):
        obj = object.__new__(self.cl)
        obj.parent = self
        obj._obj_init(*args, **kwargs)

        return obj


@dataclass(frozen=True)
class DefaultParent(ParentParent):
    _binding: inspect.BoundArguments

    def __init__(self, cl, binding):
        super().__init__(cl)
        object.__setattr__(self, '_binding', binding)

        for key, value in self._binding.arguments.items():
            if key.startswith('_'):
                raise ValueError('Template params cannot begin with an underscore')

            object.__setattr__(self, key, value)

    def __repr__(self):
        binding_repr = ", ".join(
            [f"{value}" for value in self._binding.args] +
            [f"{name}={value}" for name, value in self._binding.kwargs.items()]
        )

        return f"{self.cl.__name__}({binding_repr})"


def template_new(cls, *args, _raw=False, **kwargs):
    if _raw:
        return super(cls, cls).__new__(cls, *args, **kwargs)

    value = cls._parent(*args, **kwargs)

    if value is not None:
        return value

    sig = inspect.signature(cls._parent)

    binding = sig.bind(*args, **kwargs)
    binding.apply_defaults()

    return DefaultParent(cls, binding)


TEMPLATE_NEW_UNPICKLE_ARGS = ((), {'_raw': True})


def template_getnewargs_ex(self):
    return TEMPLATE_NEW_UNPICKLE_ARGS


def template(cl):
    cl._obj_init = cl.__init__
    del cl.__init__

    cl.__new__ = template_new
    cl.__getnewargs_ex__ = template_getnewargs_ex

    return cl
