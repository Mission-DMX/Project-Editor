"""Contains Platform StageObject."""
from __future__ import annotations

from typing import override

from model.visualizer.stage.paths import DEFAULT_MODEL_PATHS
from model.visualizer.stage.stage_object import StageObject


class Platform(StageObject):
    """Static stage floor. Every stage has exactly one."""

    DEFAULT_POSITION = (-23.0, 0.0, 0.0)

    def __init__(self, object_id: str = "platform", position: tuple[float, float, float] | None = None,
                 rotation: tuple[float, float, float] | None = None, scale: float = 1.0) -> None:
        """Initialize a new Platform StageObject."""
        super().__init__(
            object_id,
            position if position is not None else Platform.DEFAULT_POSITION,
            rotation if rotation is not None else (0.0, 0.0, 0.0),
            float(scale),
            model_path=DEFAULT_MODEL_PATHS["platform"],
        )

    @override
    def get_type(self) -> str:
        return "platform"

    @override
    def get_display_name(self) -> str:
        return "Platform"
