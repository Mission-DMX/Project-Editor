from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ModelEntry:
    """One mesh to render for a stage object, with optional local transforms.

    ``local_ops`` entries are applied before the object's world transform
    and take the form ``("translate", (x, y, z))`` or
    ``("rotate", (degrees, ax, ay, az), pivot=(px, py, pz))``.
    """

    model_path: str
    local_ops: tuple[tuple[str, Any], ...] = ()


# Keys exposed by the "Add Fixture" dialog.
FIXTURE_KEYS = [
    "truss_default",
    "truss_2point_medium",
    "truss_cross",
    "truss_long",
    "truss_medium",
    "moving_head",
]
