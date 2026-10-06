"""Subclass hierarchy for Filter / VirtualFilter.

This package replaces the previous "construct a bare :class:`model.filter.Filter` and let the
corresponding GUI node populate its I/O signature" pattern with one Filter subclass per
:class:`model.filter.FilterTypeEnumeration` value. Subclasses live in modules mirroring the
layout of ``src/view/show_mode/editor/nodes/impl/`` and declare their behaviour in the model
layer so a filter is fully usable the moment it is constructed, without requiring the editor
view to be opened. See :mod:`model.filters.factory` for the registry and the unified
construction entry point.

Submodules are imported here so that the ``@register_filter`` decorator applied in each file
runs on package import; this is what populates ``factory._FILTER_TYPE_TO_CLASS``. Adding a
new category means adding a new import below.
"""

from . import (  # side-effect import so @register_filter runs
    adapters,
    arithmetics,
    constants,
    debug,
    trigonometrics,
)
