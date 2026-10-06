"""Unified factory for :class:`model.filter.Filter` and :class:`model.filter.VirtualFilter`.

This module owns the registry mapping :class:`~model.filter.FilterTypeEnumeration` values to
Filter subclasses. :func:`construct_filter_instance` is the single construction entry point
used by the show-file loader, :meth:`~model.filter.Filter.copy`, and the editor's node base
class. When a type has no registered subclass yet, the factory falls back to the legacy
construction path (a bare :class:`~model.filter.Filter` for native types and
:func:`~model.virtual_filters.vfilter_factory._construct_virtual_filter_instance_legacy` for
virtual types) so the refactor can land incrementally.
"""

from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING

from model.filter import Filter

if TYPE_CHECKING:
    from collections.abc import Callable

    from model import Scene

logger = getLogger(__name__)

_FILTER_TYPE_TO_CLASS: dict[int, type[Filter]] = {}


def register_filter(filter_type: int) -> Callable[[type[Filter]], type[Filter]]:
    """Return a decorator that registers ``cls`` as the canonical class for ``filter_type``.

    Later registrations override earlier ones and emit a warning so accidental duplicate
    registrations are visible during startup.
    """
    key = int(filter_type)

    def wrap(cls: type[Filter]) -> type[Filter]:
        existing = _FILTER_TYPE_TO_CLASS.get(key)
        if existing is not None and existing is not cls:
            logger.warning(
                "Filter type %s already registered to %s, replacing with %s",
                key,
                existing.__name__,
                cls.__name__,
            )
        _FILTER_TYPE_TO_CLASS[key] = cls
        return cls

    return wrap


def construct_filter_instance(
    scene: Scene,
    filter_type: int,
    filter_id: str,
    pos: tuple[int, int] | tuple[float, float] | None = None,
    filter_configurations: dict[str, str] | None = None,
    initial_parameters: dict[str, str] | None = None,
) -> Filter | None:
    """Construct a :class:`~model.filter.Filter` or :class:`~model.filter.VirtualFilter`.

    The call is dispatched to a registered subclass when one exists for ``filter_type``.
    Otherwise it falls back to the legacy construction path and, for the fallback, applies
    the provided ``filter_configurations`` and ``initial_parameters`` to the resulting
    instance after construction (since legacy constructors do not accept them).

    Returns ``None`` for virtual-filter type codes whose legacy factory returns ``None`` to
    signal "not yet implemented" (e.g. :attr:`FilterTypeEnumeration.VFILTER_UNIVERSE`).
    """
    type_code = int(filter_type)
    cls = _FILTER_TYPE_TO_CLASS.get(type_code)
    if cls is not None:
        return cls(
            scene=scene,
            filter_id=filter_id,
            filter_type=type_code,
            pos=pos,
            filter_configurations=filter_configurations,
            initial_parameters=initial_parameters,
        )

    if type_code < 0:
        from model.virtual_filters.vfilter_factory import _construct_virtual_filter_instance_legacy

        instance = _construct_virtual_filter_instance_legacy(scene, type_code, filter_id, pos=pos)
        if instance is None:
            return None
        if filter_configurations:
            instance.filter_configurations.update(filter_configurations)
        if initial_parameters:
            instance.initial_parameters.update(initial_parameters)
        return instance

    return Filter(
        scene=scene,
        filter_id=filter_id,
        filter_type=type_code,
        pos=pos,
        filter_configurations=filter_configurations,
        initial_parameters=initial_parameters,
    )
