from __future__ import annotations

import inspect
from enum import Enum

from typing import (
    Callable,
    Concatenate,
    Generic,
    Optional,
    ParamSpec,
    TypeVar,
    Any,
    cast as tcast,
)

from dataclasses import dataclass, fields, make_dataclass

__all__ = "Template", "Parent", "parent_method", "parent"

parent_method = classmethod

P = ParamSpec("P")
T = TypeVar("T", bound="Template")
R = TypeVar("R")

# No real reason to annotate this well, we make the type checker think that parent_method is classmethod anyway.
@dataclass
class _parent_method(Generic[T]):
    func: Any

    def __get__(self, instance: T, owner: Optional[type[T]] = None) -> Any:
        if instance is None:
            return self

        f = self.func
        p = instance.parent

        try:
            getter = f.__get__
        except AttributeError:
            return bound_parent_method(f, p)
        else:
            return getter(p, owner)


globals()["parent_method"] = _parent_method


@dataclass
class bound_parent_method(Generic[P, R, T]):
    func: Callable[Concatenate[T, P], R]
    val: T

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        return self.func(self.val, *args, **kwargs)


@dataclass(frozen=True, repr=False, slots=True)
class Parent:
    cl: type

    def __call__(self, *args: Any, **kwargs: Any):
        res = object.__new__(self.cl)
        res.parent = self
        res.__init__(*args, **kwargs)

        return res

    def __getattr__(self, name: str):
        if name.startswith("_"):
            raise AttributeError(f"{type(self)} {name}")

        res: Any = getattr(object.__getattribute__(self, "cl"), name)

        if isinstance(res, _parent_method):
            res = res.__get__(self) # type: ignore

        return res

    def __repr__(self):
        return f"{self.cl.__qualname__}[{', '.join(str(getattr(self, field.name)) for field in fields(self)[1:])}]"


Self = TypeVar("Self")


class NewNoneType(Enum):
    NewNone = 0


NewNone = NewNoneType.NewNone


def get_fields(cl: type) -> dict[str, tuple[Optional[str], Any | NewNoneType]]:
    annots = inspect.get_annotations(cl)
    keys = set(annots.keys()).union(cl.__dict__.keys())

    return {key: (annots.get(key), cl.__dict__.get(key, NewNone)) for key in keys}


def parse_parent_var(annot: str) -> Optional[str]:
    if annot.startswith("ClassVar[") and annot.endswith("]"):
        return annot[9:-1]

    return None


@dataclass
class ParentDeferProperty:
    attr_name: str

    def __get__(self, instance: Template, owner: Optional[type] = None) -> Any:
        return getattr(instance.parent, self.attr_name)


TEMPLATE_NEW_UNPICKLE_ARGS = ((), {"_unpickling": True})


class Template:
    """
    Classes deriving from this class are templates.

    Template parameters are declared as dataclass parameters, but should be annotated as ClassVar-s.
    See test_template_tools for examples.

    To define template fields, declare them as ClassVars.
    To define parent methods (and properties), use the parent_method decorator.
    To define parent dunder methods, write them normally, but prefix the name with "_parent". Do not use the parent_method decorator.
    """

    _Parent: type[Parent]
    parent: Parent

    def __new__(cls, *_args: Any, _unpickling: bool = False, **_kwargs: Any):
        if _unpickling:
            return object.__new__(cls)
        raise TypeError(f"Template class {cls.__qualname__} instantiated directly.")

    @staticmethod
    def __getnewargs_ex__():
        return TEMPLATE_NEW_UNPICKLE_ARGS

    def __class_getitem__(cls: type[Self], args: Any) -> type[Self]:
        return cls._Parent(cls, *args) if isinstance(args, tuple) else cls._Parent(cls, args)  # type: ignore - this is actually a parent and not a deriving class, but it should behave similarly.

    def __init_subclass__(cls) -> None:
        dct: dict[str, tuple[Optional[str], Any | NewNoneType]] = {}

        for scls in cls.mro()[::-1]:
            dct.update(get_fields(scls))

        fields: dict[str, tuple[str, Any | NewNoneType]] = {}
        for key, (annot, val) in dct.items():
            if annot is None:
                continue

            inner_annot = parse_parent_var(annot)
            if inner_annot is None:
                continue

            fields[key] = (inner_annot, val)

        content: dict[str, Any] = {
            key[7:]: val for key, (_, val) in dct.items() if key.startswith("_parent")
        }
        content["__module__"] = cls.__module__

        cls._Parent = tcast(  # the type checker doesn't understand the inheritance.
            type[Parent],
            make_dataclass(
                f"{cls.__name__}._Parent",
                [  # annot is a str, but the make_dataclass signature wrongly says it should be a type.
                    (key, tcast(type, annot)) + (() if val is NewNone else (val,))
                    for key, (annot, val) in fields.items()
                ],
                bases=(Parent,),
                namespace=content,
                frozen=True,
                slots=True,
                repr=False,
            ),
        )

        for key in fields.keys():
            setattr(cls, key, ParentDeferProperty(key))


def parent(x: Self) -> type[Self]:
    if isinstance(x, Template):
        return x.parent
    return type(x)
