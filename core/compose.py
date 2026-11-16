"""Function composition utilities for Lab 7.

Pure, dependency-free building blocks used by the service facades:

- ``compose(f, g, h)(x) == f(g(h(x)))``  (right-to-left, mathematical order)
- ``pipe(x, f, g, h)  == h(g(f(x)))``    (left-to-right, data-flow order)
- ``all_of(p, q, ...)``: combine predicates into one (logical AND).
- ``rank_by(key_fns)``: build a pure ordering function from key functions.
"""

from __future__ import annotations

import functools
from collections.abc import Callable, Iterable
from typing import Any, TypeVar

T = TypeVar("T")


def _identity(x: T) -> T:
    return x


def compose(*funcs: Callable[[Any], Any]) -> Callable[[Any], Any]:
    """Compose unary functions right-to-left: ``compose(f, g)(x) == f(g(x))``.

    ``compose()`` with no functions is the identity function.
    """
    if not funcs:
        return _identity

    def composed(x: Any) -> Any:
        return functools.reduce(lambda acc, fn: fn(acc), reversed(funcs), x)

    return composed


def pipe(x: Any, *funcs: Callable[[Any], Any]) -> Any:
    """Thread ``x`` through unary functions left-to-right: ``pipe(x, f, g) == g(f(x))``.

    ``pipe(x)`` with no functions returns ``x`` unchanged.
    """
    return functools.reduce(lambda acc, fn: fn(acc), funcs, x)


def all_of(*predicates: Callable[[T], bool]) -> Callable[[T], bool]:
    """Combine predicates with logical AND. No predicates means "accept everything"."""

    def combined(item: T) -> bool:
        return all(p(item) for p in predicates)

    return combined


def rank_by(
    key_fns: tuple[Callable[[T], Any], ...],
) -> Callable[[Iterable[T]], Iterable[T]]:
    """Build an ordering function from key functions (lexicographic, ascending).

    With no key functions the input is returned untouched, so a lazy stream stays lazy.
    Otherwise a new sorted tuple is returned and the input is never mutated.
    """

    def ranker(items: Iterable[T]) -> Iterable[T]:
        if not key_fns:
            return items
        return tuple(sorted(items, key=lambda it: tuple(k(it) for k in key_fns)))

    return ranker
