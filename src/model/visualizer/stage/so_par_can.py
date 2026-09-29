"""Contains ParCan."""

from __future__ import annotations

from typing import Any, override

from PySide6.QtGui import QVector3D

from model.visualizer.stage.model_entries import ModelEntry
from model.visualizer.stage.paths import DEFAULT_MODEL_PATHS
from model.visualizer.stage.stage_object import LenseLight, StageObject


class ParCan(StageObject):
    """Fixed-direction PAR can with a coloured beam and lens.

    Behaves like :class:`MovingHead` for DMX-driven colour and dimmer, but has
    no pan/tilt actuator: the beam always shoots along the model's local ``+Y``
    axis (rotated by the object's Euler rotation).

    The bundled ``par_can.glb`` model has its base at ``Y = 0`` and the tube
    opening at ``Y ≈ 85`` in model units. The lens billboard is placed just
    inside the tube so it looks recessed, and the volumetric beam originates
    from that same point.
    """

    # Distance from the object origin (base of the tube) to the lens plane, in
    # the model's local units. Consumed by ``Stage3DWidget`` via
    # ``beam_local_origin`` and scaled by ``self.scale`` at render time.
    beam_local_origin = QVector3D(0.0, 80.0, 0.0)

    # Diameter (world units at ``scale == 1``) of the emissive disc rendered
    # inside the tube. The tube's outer diameter in the model is ~65 units, so
    # 50 leaves a small dark rim between disc and tube wall.
    LENS_DIAMETER = 50.0

    DEFAULT_SCALE = 0.05

    def __init__(
        self,
        object_id: str,
        position: tuple[float, float, float] | None = None,
        rotation: tuple[float, float, float] | None = None,
        scale: float = DEFAULT_SCALE,
        beam_on: bool = True,
        beam_color: tuple[int, int, int] | None = None,
        dimmer: float = 1.0,
    ) -> None:
        """Initialize a PAR can stage object."""
        super().__init__(object_id, position, rotation, float(scale), model_path=None)

        if beam_color is None:
            beam_color = (255, 255, 255)
        r, g, b = beam_color
        self.beam_color: tuple[int, int, int] = (int(r), int(g), int(b))
        self.dimmer: float = max(0.0, min(1.0, float(dimmer)))
        self.beam_on: bool = bool(beam_on)

    @override
    def get_type(self) -> str:
        return "par_can"

    @override
    def get_display_name(self) -> str:
        return "PAR Can"

    @override
    def get_model_entries(self) -> list[ModelEntry]:
        return [ModelEntry(DEFAULT_MODEL_PATHS["par_can"])]

    @property
    def lense_colors(self) -> list[LenseLight]:
        """Single emissive disc placed at the beam origin (inside the tube).

        Recomputed each frame so the disc's size tracks the object's ``scale``
        and its colour tracks the DMX-updated ``beam_color``. Left/right and
        vertical offset are zero, so the disc sits exactly on the beam axis at
        :attr:`beam_local_origin` (see :meth:`Stage3DWidget._collect_lense_lights`).
        """
        size = ParCan.LENS_DIAMETER * float(self.scale)
        return [
            LenseLight(
                position=QVector3D(0.0, 0.0, 0.0),
                rotation=QVector3D(0.0, 0.0, 0.0),
                size=size,
                color=self.beam_color,
                origin_node="",
                tilt_node="",
            )
        ]

    def _has_dimmer_channel(self) -> bool:
        """Whether the linked device declares a dimmer channel."""
        dc = self.device_config
        if not dc:
            return False
        # Match the MovingHead schema: ``movement.mapping.dimmer`` holds the offset.
        return dc.get("movement", {}).get("mapping", {}).get("dimmer", -1) >= 0

    def update_beam_state(self) -> None:
        """Recompute ``beam_on`` (and ``dimmer`` if no dimmer channel is mapped)."""
        color = self.beam_color
        any_color = color[0] > 0 or color[1] > 0 or color[2] > 0
        if self._has_dimmer_channel():
            self.beam_on = self.dimmer > 0 and any_color
        else:
            self.beam_on = any_color
            if any_color:
                self.dimmer = 1.0

    @override
    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data.update(
            {
                "beam_on": bool(self.beam_on),
                "beam_color": {
                    "r": int(self.beam_color[0]),
                    "g": int(self.beam_color[1]),
                    "b": int(self.beam_color[2]),
                },
                "dimmer": float(self.dimmer),
            }
        )
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ParCan:
        """Construct a PAR can from parsed data."""
        pos = data.get("position", {}) or {}
        rot = data.get("rotation", {}) or {}
        position = (float(pos.get("x", 0.0)), float(pos.get("y", 0.0)), float(pos.get("z", 0.0)))
        rotation = (float(rot.get("x", 0.0)), float(rot.get("y", 0.0)), float(rot.get("z", 0.0)))
        scale = float(data.get("scale", cls.DEFAULT_SCALE))
        beam_on = bool(data.get("beam_on", True))
        dimmer = float(data.get("dimmer", 1.0))

        bc = data.get("beam_color") or {}
        if isinstance(bc, dict):
            beam_color = (int(bc.get("r", 255)), int(bc.get("g", 255)), int(bc.get("b", 255)))
        elif isinstance(bc, (list, tuple)) and len(bc) >= 3:
            beam_color = (int(bc[0]), int(bc[1]), int(bc[2]))
        else:
            beam_color = (255, 255, 255)

        obj = cls(
            data.get("id", ""),
            position=position,
            rotation=rotation,
            scale=scale,
            beam_on=beam_on,
            beam_color=beam_color,
            dimmer=dimmer,
        )
        obj.name = data.get("name", "")
        obj.device_config = data.get("device")

        # Match MovingHead's behaviour of resetting DMX-controlled values so they
        # come from live data rather than stale state stored in the yaml.
        if obj.device_config:
            dc = obj.device_config
            mv_map = dc.get("movement", {}).get("mapping", {})
            col_map = dc.get("color", {}).get("mapping", {})
            has_dimmer = mv_map.get("dimmer", -1) >= 0
            has_color = any(col_map.get(role, -1) >= 0 for role in ("red", "green", "blue", "white"))
            if has_dimmer:
                obj.dimmer = 1.0
            if has_color:
                obj.beam_color = (0, 0, 0)
            if has_dimmer or has_color:
                obj.update_beam_state()

        return obj
