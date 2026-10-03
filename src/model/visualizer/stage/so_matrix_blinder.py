"""Contains MatrixBlinder StageObject."""

from __future__ import annotations

from typing import Any, override

from model.visualizer.stage.so_pixel_fixture import PixelFixture


class MatrixBlinder(PixelFixture):
    """Matrix blinder with a 2D grid of pixels on its front face."""

    DEFAULT_MATRIX = (4, 2)
    DEFAULT_SIZE = (400.0, 200.0, 150.0)
    DEFAULT_SCALE = 0.05

    def __init__(
        self,
        object_id: str,
        pixel_matrix: tuple[int, int] | None = None,
        physical_size: tuple[float, float, float] | None = None,
        position: tuple[float, float, float] | None = None,
        rotation: tuple[float, float, float] | None = None,
        scale: float | None = None,
        pixel_colors: list[tuple[int, int, int]] | None = None,
    ) -> None:
        """Initialize a new MatrixBlinder stage object."""
        super().__init__(
            object_id,
            pixel_matrix=pixel_matrix if pixel_matrix is not None else MatrixBlinder.DEFAULT_MATRIX,
            physical_size=physical_size if physical_size is not None else MatrixBlinder.DEFAULT_SIZE,
            position=position,
            rotation=rotation,
            scale=scale if scale is not None else MatrixBlinder.DEFAULT_SCALE,
            pixel_colors=pixel_colors,
        )

    @override
    def get_type(self) -> str:
        return "matrix_blinder"

    @override
    def get_display_name(self) -> str:
        cols, rows = self.pixel_matrix
        return f"Matrix Blinder ({cols}x{rows})"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MatrixBlinder:
        """Construct an instance from parsed data."""
        matrix = cls._read_pixel_matrix(data, cls.DEFAULT_MATRIX)
        size = cls._read_physical_size(data, cls.DEFAULT_SIZE)
        position, rotation, scale = cls._read_common_transform(data, cls.DEFAULT_SCALE)
        obj = cls(
            data.get("id", ""),
            pixel_matrix=matrix,
            physical_size=size,
            position=position,
            rotation=rotation,
            scale=scale,
        )
        obj.name = data.get("name", "")
        obj.device_config = data.get("device")
        return obj
