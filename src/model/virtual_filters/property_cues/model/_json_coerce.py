"""JSON round-trip helpers shared between the model and the editor view."""

from __future__ import annotations

from typing import Any


def coerce_int_keys(mapping: Any) -> Any:  # noqa: ANN401
    """Return ``mapping`` with its keys coerced to int when they are all decimal integers.

    ``json.dumps`` stringifies every dict key — so a value authored as
    ``{0: 3, 1: 7}`` comes back as ``{"0": 3, "1": 7}``. Downstream lookups
    with an integer key would miss every entry. If every key in ``mapping``
    parses as a decimal integer, this helper returns a new dict keyed by
    those ints; otherwise ``mapping`` is returned untouched. Non-dict
    inputs are passed through unchanged so this helper is safe to call
    unconditionally from recursive JSON walkers.
    """
    if not isinstance(mapping, dict) or not mapping:
        return mapping
    coerced: dict[int, Any] = {}
    for key, value in mapping.items():
        try:
            coerced[int(key)] = value
        except (TypeError, ValueError):
            return mapping
    return coerced
