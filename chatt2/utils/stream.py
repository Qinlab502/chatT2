from __future__ import annotations

from inspect import isgeneratorfunction
from types import GeneratorType
from typing import TYPE_CHECKING, Generic, overload

if TYPE_CHECKING:
    from typing import Callable, Generator, ParamSpec, TypeVar

    P = ParamSpec("P")
    Yield = TypeVar("Yield")
    Return = TypeVar("Return")

    @overload
    def streamable(func: Callable[P, Generator[Yield, None, Return]]) -> Streamable[P, Yield, Return]: ...
    @overload
    def streamable(func: Callable[P, Return]) -> Callable[P, Return]: ...


def streamable(func):
    return Streamable(func) if isgeneratorfunction(func) else func


class Streamable(Generic[P, Yield, Return] if TYPE_CHECKING else object):
    def __init__(self, func: Callable[P, Generator[Yield, None, Return]]):
        self.stream = func

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> Return:
        it = self.stream(*args, **kwargs)

        if not isinstance(it, GeneratorType):
            return it  # type: ignore

        try:
            while True:
                next(it)
        except StopIteration as e:
            return e.value


__all__ = ["streamable"]


if __name__ == "__main__":

    @streamable
    def f():
        yield 2
        return 123

    assert f() == 123

    for i in f.stream():
        assert i == 2

    @streamable
    def g():
        return 234

    assert g() == 234
