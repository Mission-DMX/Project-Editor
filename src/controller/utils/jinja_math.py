"""Jinja ``Environment`` factory with integer math filters.

Used by both :mod:`controller.cli.connect_command` (for user-authored
``connect`` expressions) and the property-based cue vfilter's preset
evaluator. Kept here so the two callers share one authoritative set of
filters -- any new filter added for one is immediately available to the
other.
"""

from __future__ import annotations

from jinja2 import Environment, StrictUndefined


def _add(value: str, arg: str) -> str:
    return str(int(int(value) + int(arg)))


def _sub(value: str, arg: str) -> str:
    return str(int(int(value) - int(arg)))


def _mul(value: str, arg: str) -> str:
    return str(int(int(value) * int(arg)))


def _div(value: str, arg: str) -> str:
    """Divide the given value by the given divisor using integer floor division."""
    divisor = int(arg)
    if divisor == 0:
        raise ValueError("The 'div' filter requires a divisor other than zero.")
    return str(int(value) // divisor)


def _mod(value: str, arg: str) -> str:
    """Compute the integer modulo of the given value by the given divisor."""
    divisor = int(arg)
    if divisor == 0:
        raise ValueError("The 'mod' filter requires a divisor other than zero.")
    return str(int(int(value) % divisor))


def get_math_enabled_jinja_env() -> Environment:
    """Return a Jinja environment with the math filters (``add``, ``sub``, ``mul``, ``div``, ``mod``)."""
    env = Environment(undefined=StrictUndefined)  # noqa: S701 the editor is not a web page.
    env.filters["add"] = _add
    env.filters["sub"] = _sub
    env.filters["mul"] = _mul
    env.filters["div"] = _div
    env.filters["mod"] = _mod
    return env
