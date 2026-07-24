"""Contains Truss."""
from __future__ import annotations

from typing import Any, override

from model.visualizer.stage.paths import DEFAULT_MODEL_PATHS
from model.visualizer.stage.stage_object import StageObject


class Truss(StageObject):
    """Truss fixture (default, cross, long, medium, 2-point)."""

    def __init__(self, object_id: str, variant: str = "default",
                 position: tuple[float, float, float] | None = None,
                 rotation: tuple[float, float, float] | None = None, scale: float = 1.0) -> None:
        """Initialize Truss StageObject."""
        self.variant = variant

        key = f"truss_{variant}" if variant != "" else "truss"
        if key not in DEFAULT_MODEL_PATHS:
            key = "truss_default"
            self.variant = "default"

        super().__init__(
            object_id, position, rotation, float(scale),
            model_path=DEFAULT_MODEL_PATHS[key],
        )

    @override
    def get_type(self) -> str:
        return f"truss_{self.variant}" if self.variant != "" else "truss"

    @override
    def get_display_name(self) -> str:
        mapping = {
            "default": "Truss Default",
            "2point_medium": "Truss 2-Point",
            "cross": "Truss Cross",
            "long": "Truss Long",
            "medium": "Truss Medium",
        }
        return mapping.get(self.variant, f"Truss {self.variant}")

    @override
    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data["variant"] = self.variant
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Truss:
        """Construct instance from parsed data."""
        object_id = data.get("id")
        pos = data.get("position", {})
        rot = data.get("rotation", {})
        position = (pos.get("x", 0.0), pos.get("y", 0.0), pos.get("z", 0.0))
        rotation = (rot.get("x", 0.0), rot.get("y", 0.0), rot.get("z", 0.0))

        # Variant may be explicit or embedded in legacy type strings like "truss_cross".
        t = (data.get("type") or "truss").lower()
        variant = data.get("variant")
        if not variant:
            if t == "truss":
                variant = "default"
            elif t.startswith("truss_"):
                variant = t[len("truss_"):]
            else:
                variant = "default"

        scale = float(data.get("scale", 1.0))
        obj = cls(object_id, variant=variant, position=position,
                  rotation=rotation, scale=scale)
        obj.name = data.get("name", "")
        obj.device_config = data.get("device")
        return obj
