"""Contains StageObject base class."""

from __future__ import annotations

from typing import Any

from PySide6.QtGui import QVector3D

from model.visualizer.stage.model_entries import ModelEntry
from model.visualizer.stage.paths import DEFAULT_MODEL_PATHS


class LenseLight:
    """PoD class for lense light data."""

    __slots__ = ["color", "origin_node_name", "position", "rotation", "size", "tilt_node_name"]
    def __init__(self, position: QVector3D | None = None,
                 rotation: QVector3D | None = None,
                 size: float = 1.0,
                 color: tuple[int, int, int] = (255, 255, 255),
                 origin_node: str = "", tilt_node: str = "") -> None:
        """Initialize new light."""
        self.position: QVector3D = QVector3D(0.0, 0.0, 0.0) if position is None else position
        self.rotation: QVector3D = QVector3D(0.0, 0.0, 0.0) if rotation is None else rotation
        self.size: float = size
        self.color: tuple[int, int, int] = color
        self.origin_node_name: str = origin_node
        self.tilt_node_name: str = tilt_node


class StageObject:
    """Base class for anything placed on the stage.

    An implementing class may provide additional attributes which are checked while rendering.
    For performance reasons, they are not provided as mixin classes. Here's a full list:
     * `beam_on` (bool) if provided the StageObject (SO) has a light beam to be rendered. True/False indicates
        visibility. Having disabled beams still consumes resources.
     * `pan` and `tilt` (float) pan and tilt coordinates for movable part and beam
     * `beam_color` (tuple[int, int, int]) RGB color of beam (if present). Range 0 to 255
     * `dimmer` (float) brightness multiplier
     * `lense_colors` (list[tuple[vec3[float], vec3[float], float, vec3[int], str, str]]) a list containing lense
       illumination descriptions (position, rotation, size, color(rgb 0-255)). For each entry a lense illumination
       will be drawn. Positions are relative to model base position as defined by the provided node (name,
       base_node_name and tilt_node_name). If the fixture does not have pan/tilt capabilities, the strings can be empty.

    """

    def __init__(
        self,
        object_id: str,
        position: tuple[float, float, float] | None = None,
        rotation: tuple[float, float, float] | None = None,
        scale: float | None = None,
        model_path: str | None = None,
    ) -> None:
        """Initialize base stage object data structures."""
        self.id = object_id
        self.name = ""
        self.position = position if position is not None else (0.0, 0.0, 0.0)
        self.rotation = rotation if rotation is not None else (0.0, 0.0, 0.0)
        self.scale = float(scale) if scale is not None else 1.0
        self.model_path = model_path

        # Optional link to a real DMX device (universe, start_channel, mapping).
        self.device_config: dict[str, Any] | None = None

        if self.model_path is None:
            key = self.get_type().lower()
            if key in DEFAULT_MODEL_PATHS:
                self.model_path = DEFAULT_MODEL_PATHS[key]

    def get_type(self) -> str:
        """Get the type of this stage object."""
        return "default"

    def get_display_name(self) -> str:
        """Get the human readable name of this stage object."""
        return self.get_type()

    def get_model_entries(self) -> list[ModelEntry]:
        """One or more render entries. Composite fixtures override this."""
        if not self.model_path:
            return []
        return [ModelEntry(self.model_path)]

    def to_dict(self) -> dict[str, Any]:
        """Get a dictionary representation of this object, suitable for serialization."""
        d = {
            "id": self.id,
            "name": self.name,
            "type": self.get_type(),
            "position": {"x": self.position[0], "y": self.position[1], "z": self.position[2]},
            "rotation": {"x": self.rotation[0], "y": self.rotation[1], "z": self.rotation[2]},
            "scale": self.scale,
        }
        if self.device_config:
            d["device"] = self.device_config
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StageObject:
        """Instantiate from deserialized data."""
        object_id = data.get("id")
        pos = data.get("position", {})
        rot = data.get("rotation", {})
        position = (pos.get("x", 0.0), pos.get("y", 0.0), pos.get("z", 0.0))
        rotation = (rot.get("x", 0.0), rot.get("y", 0.0), rot.get("z", 0.0))
        scale = float(data.get("scale", 1.0))
        obj = cls(object_id, position, rotation, scale)
        obj.name = data.get("name", "")
        obj.device_config = data.get("device")
        return obj
