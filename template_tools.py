from __future__ import annotations
import inspect
from typing import Callable, ClassVar, TypeVar, Any, get_args, get_origin

from dataclasses import dataclass
from functools import cache

__all__ = "Template", "Parent", "parent_method"

parent_method = classmethod


@dataclass
class _parent_method:
    func: Callable

    def __get__(self, instance, owner=None):
        if instance is None:
            return self

        if hasattr(self.func, "__get__"):
            return self.func.__get__(instance, owner)

        return bound_parent_method(self.func, instance)


globals()["parent_method"] = _parent_method


@dataclass
class bound_parent_method:
    func: Callable
    val: Any

    def __call__(self, *args, **kwargs):
        return self.func(self.val, *args, **kwargs)


@dataclass(frozen=True, slots=True)
class Parent:
    cl: type

    def __call__(self, *args: Any, **kwargs: Any):
        res = object.__new__(self.cl)
        res.parent = self
        res.__init__(*args, **kwargs)

        return res

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(f"{type(self)} {name}")

        res = getattr(object.__getattribute__(self, "cl"), name)

        if isinstance(res, _parent_method):
            res = res.__get__(self)

        return res


Self = TypeVar("Self")


class NewNoneType:
    pass


NewNone = NewNoneType()


def get_fields(cl: type) -> dict[str, tuple[Any, Any]]:
    annots = inspect.get_annotations(cl, eval_str=True)
    keys = set(annots.keys()).union(cl.__dict__.keys())

    return {
        key: (annots.get(key, NewNone), cl.__dict__.get(key, NewNone)) for key in keys
    }


class Template:
    _Parent: type[Parent]
    ParentExtras: type[Parent] = Parent
    parent: Parent

    def __class_getitem__(cls: type[Self], args: Any) -> type[Self]:
        return cls._Parent(cls, *args) if isinstance(args, tuple) else cls._Parent(cls, args)  # type: ignore - this is actually a parent and not a deriving class, but it should behave similarly.

    def __init_subclass__(cls) -> None:
        dct = {}

        for scls in cls.mro()[::-1]:
            dct.update(get_fields(scls))

        fields = {}

        for key, (annot, val) in dct.items():
            if get_origin(annot) is ClassVar:
                (type_,) = get_args(annot)
                fields[key] = (type_, val)

        content = {
            key: val for key, (annot, val) in fields.items() if val is not NewNone
        }
        content["__annotations__"] = {
            key: annot for key, (annot, _val) in fields.items()
        }
        content["__module__"] = cls.__module__

        cls._Parent = dataclass(frozen=True)(
            type(
                f"{cls.__name__}._Parent",
                (cls.ParentExtras,),
                content,
            )
        )

        for key in fields.keys():
            setattr(cls, key, property(lambda self: getattr(self.parent, key)))


def parent(x: Self) -> type[Self]:
    if isinstance(x, Template):
        return x.parent
    return type(x)
