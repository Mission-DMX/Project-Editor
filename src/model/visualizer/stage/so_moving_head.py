"""Contains MovingHead."""
from __future__ import annotations

from typing import Any, override

from model.visualizer.stage.model_entries import ModelEntry
from model.visualizer.stage.paths import DEFAULT_MODEL_PATHS
from model.visualizer.stage.stage_object import StageObject

from PySide6.QtGui import QVector3D

class MovingHead(StageObject):
    """Moving head with pan/tilt control and colored beam.

    Loaded from a single .glb file whose node hierarchy the renderer
    overrides per frame using the axis-angle pairs from
    ``get_gltf_node_overrides()``.
    """

    # Names of the joint nodes inside the .glb model.
    PAN_NODE_NAME = "Cube.035"
    TILT_NODE_NAME = "Cylinder.018"
    BEAM_ORIGIN_NODE_NAME = "BeamOrigin"

    PAN_AXIS = (0.0, 1.0, 0.0)
    TILT_AXIS = (1.0, 0.0, 0.0)

    def __init__(
        self,
        object_id: str,
        channels: int = 16,
        position: tuple[float, float, float] | None = None,
        rotation: tuple[float, float, float] | None = None,
        scale: float = 20.0,   # .glb is small; scale up for visibility
        pan: float = 0.0,
        tilt: float = 0.0,
        beam_on: bool = True,
        beam_color: tuple[int, int, int] | None = None,
        dimmer: float = 1.0,
    ) -> None:
        """Initialize MovingHead stage object."""
        # Must be set before super().__init__ since get_type() reads it.
        self.channels = 8 if int(channels) == 8 else 16
        super().__init__(object_id, position, rotation, float(scale), model_path=None)

        self.pan = float(pan)
        self.tilt = float(tilt)
        self.beam_on = bool(beam_on)

        if beam_color is None:
            beam_color = (0, 255, 0)
        r, g, b = beam_color
        self.beam_color = (int(r), int(g), int(b))
        self.dimmer = max(0.0, min(1.0, float(dimmer)))
        self.lense_colors = [(
            QVector3D(1,1,1),  # position
            QVector3D(1,1,1),  # rotation
            10.0,  # size
            (255, 255, 255),  # current color
            "BeamOrigin",  # origin node name
            "Cylinder.018")  # name of movable node
        ]

    @override
    def get_type(self) -> str:
        return "moving_head"

    @override
    def get_display_name(self) -> str:
        return "Moving Head"

    @override
    def get_model_entries(self) -> list[ModelEntry]:
        return [ModelEntry(DEFAULT_MODEL_PATHS["moving_head"])]

    def get_gltf_node_overrides(self) -> dict[str, tuple[float, float, float, float]]:
        """Axis-angle overrides for pan and tilt: ``{node: (ax, ay, az, deg)}``."""
        return {
            MovingHead.PAN_NODE_NAME:  (*MovingHead.PAN_AXIS, float(self.pan)),
            MovingHead.TILT_NODE_NAME: (*MovingHead.TILT_AXIS, float(self.tilt)),
        }

    @override
    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data.update({
            "pan": self.pan,
            "tilt": self.tilt,
            "channels": self.channels,
            "beam_on": bool(self.beam_on),
            "beam_color": {
                "r": int(self.beam_color[0]),
                "g": int(self.beam_color[1]),
                "b": int(self.beam_color[2]),
            },
            "dimmer": float(self.dimmer),
        })
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MovingHead:
        """Construct an instance from parsed data."""
        object_id = data.get("id")
        pos = data.get("position", {})
        rot = data.get("rotation", {})
        position = (pos.get("x", 0.0), pos.get("y", 0.0), pos.get("z", 0.0))
        rotation = (rot.get("x", 0.0), rot.get("y", 0.0), rot.get("z", 0.0))
        pan = float(data.get("pan", 0.0))
        tilt = float(data.get("tilt", 0.0))
        beam_on = bool(data.get("beam_on", True))

        bc = data.get("beam_color") or {}
        if isinstance(bc, dict):
            beam_color = (int(bc.get("r", 0)), int(bc.get("g", 255)), int(bc.get("b", 0)))
        elif isinstance(bc, (list, tuple)) and len(bc) >= 3:
            beam_color = (int(bc[0]), int(bc[1]), int(bc[2]))
        else:
            beam_color = (0, 255, 0)

        t = (data.get("type") or "moving_head_16ch").lower()
        channels = int(data.get("channels", 8 if t.endswith("8ch") else 16))
        dimmer = float(data.get("dimmer", 1.0))
        scale = float(data.get("scale", 20.0))

        obj = cls(
            object_id,
            channels=channels,
            position=position,
            rotation=rotation,
            scale=scale,
            pan=pan,
            tilt=tilt,
            beam_on=beam_on,
            beam_color=beam_color,
            dimmer=dimmer,
        )
        obj.name = data.get("name", "")
        obj.device_config = data.get("device")

        # Reset DMX-controlled values so they come from live data, not the file.
        if obj.device_config:
            dc = obj.device_config
            mv_map = dc.get("movement", {}).get("mapping", {})
            col_map = dc.get("color", {}).get("mapping", {})
            if mv_map.get("pan_coarse", -1) >= 0:
                obj.pan = 0.0
            if mv_map.get("tilt_coarse", -1) >= 0:
                obj.tilt = 0.0
            if mv_map.get("dimmer", -1) >= 0 or col_map.get("white", -1) >= 0:
                obj.dimmer = 1.0
                obj.beam_on = True

        return obj
