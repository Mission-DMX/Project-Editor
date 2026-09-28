"""Contains PixelFixture base class for LED bars and matrix blinders."""

from __future__ import annotations

from typing import Any, override

import numpy as np
from PySide6.QtGui import QMatrix4x4, QVector3D

from model.visualizer.stage.model_entries import ModelEntry
from model.visualizer.stage.stage_object import LenseLight, StageObject

# Fraction of the pixel cell reserved for the surrounding bezel.
_BEZEL_FRACTION = 0.06
# Fraction of the fixture depth by which the lens is recessed into the front face.
_RECESS_FRACTION = 0.25
# Fraction of the pixel cell size used as the emissive disc size.
_LENSE_SIZE_FRACTION = 0.9


class PixelFixture(StageObject):
    """Static pixel-based fixture (LED bar, matrix blinder).

    The front face carries a configurable grid of pixels. Each pixel is
    rendered as a small recessed square in the housing plus a bright
    billboard disc (via ``lense_colors``) that visualises its DMX colour.

    Mesh local coordinate system (matches Stage3DWidget's world convention
    ``+Y`` = up):

    * ``+X`` — width (pixel columns; col 0 is at the left)
    * ``+Y`` — height (pixel rows; row 0 is at the top)
    * ``+Z`` — depth (front face at ``z = 0`` faces ``+Z``, back at ``z = -depth``)

    Pixels are stored in row-major order (``index = row * cols + col``) with
    row 0 at the top of the fixture as seen from the front — this matches the
    ordering DMX matrix fixtures typically use.

    The class attribute :attr:`beam_local_direction` overrides the default
    upward beam-direction convention used by :class:`Stage3DWidget` so that a
    freshly placed fixture with rotation ``(0, 0, 0)`` shows its emissive
    front face toward the camera.
    """

    _MESH_KEY_PREFIX = "pixel_fixture"

    # Consumed by Stage3DWidget when computing the beam-local basis for lens
    # billboards; keeps pixel positions attached to the front face regardless
    # of how the object is rotated.
    beam_local_direction = QVector3D(0.0, 0.0, 1.0)

    def __init__(
        self,
        object_id: str,
        pixel_matrix: tuple[int, int] = (8, 1),
        physical_size: tuple[float, float, float] = (1000.0, 100.0, 100.0),
        position: tuple[float, float, float] | None = None,
        rotation: tuple[float, float, float] | None = None,
        scale: float = 0.05,
        pixel_colors: list[tuple[int, int, int]] | None = None,
    ) -> None:
        """Initialize PixelFixture."""
        cols = max(1, int(pixel_matrix[0]))
        rows = max(1, int(pixel_matrix[1]))
        self._pixel_matrix: tuple[int, int] = (cols, rows)
        w = max(1e-3, float(physical_size[0]))
        h = max(1e-3, float(physical_size[1]))
        d = max(1e-3, float(physical_size[2]))
        self._physical_size: tuple[float, float, float] = (w, h, d)

        super().__init__(object_id, position, rotation, float(scale), model_path=None)

        n = cols * rows
        default_color = (0, 0, 0)
        if pixel_colors is None:
            self._pixel_colors: list[tuple[int, int, int]] = [default_color] * n
        else:
            trimmed = [(int(r), int(g), int(b)) for r, g, b in pixel_colors[:n]]
            trimmed.extend([default_color] * (n - len(trimmed)))
            self._pixel_colors = trimmed

        self._mesh_generation: int = 0
        self._refresh_model_path()

    @property
    def pixel_matrix(self) -> tuple[int, int]:
        """Grid layout as ``(columns, rows)``."""
        return self._pixel_matrix

    @pixel_matrix.setter
    def pixel_matrix(self, value: tuple[int, int]) -> None:
        cols = max(1, int(value[0]))
        rows = max(1, int(value[1]))
        if (cols, rows) == self._pixel_matrix:
            return
        self._pixel_matrix = (cols, rows)
        n = cols * rows
        if len(self._pixel_colors) < n:
            self._pixel_colors.extend([(0, 0, 0)] * (n - len(self._pixel_colors)))
        else:
            self._pixel_colors = self._pixel_colors[:n]
        self._bump_mesh_generation()

    @property
    def physical_size(self) -> tuple[float, float, float]:
        """Displayed dimensions ``(width, height, depth)`` in the mesh's own units (mm by default)."""
        return self._physical_size

    @physical_size.setter
    def physical_size(self, value: tuple[float, float, float]) -> None:
        w = max(1e-3, float(value[0]))
        h = max(1e-3, float(value[1]))
        d = max(1e-3, float(value[2]))
        if (w, h, d) == self._physical_size:
            return
        self._physical_size = (w, h, d)
        self._bump_mesh_generation()

    @property
    def pixel_colors(self) -> list[tuple[int, int, int]]:
        """Live RGB values (0-255) for each pixel in row-major order."""
        return self._pixel_colors

    def set_pixel_color(self, index: int, color: tuple[int, int, int]) -> None:
        """Set the RGB colour of a single pixel by flat index."""
        if 0 <= index < len(self._pixel_colors):
            self._pixel_colors[index] = (int(color[0]), int(color[1]), int(color[2]))

    def _bump_mesh_generation(self) -> None:
        self._mesh_generation += 1
        self._refresh_model_path()

    def _refresh_model_path(self) -> None:
        cols, rows = self._pixel_matrix
        w, h, d = self._physical_size
        self.model_path = (
            f"{self._MESH_KEY_PREFIX}::{self.id}::{self._mesh_generation}::"
            f"{cols}x{rows}::{w:.3f}x{h:.3f}x{d:.3f}"
        )

    @override
    def get_type(self) -> str:
        return "pixel_fixture"

    @override
    def get_display_name(self) -> str:
        cols, rows = self._pixel_matrix
        return f"Pixel Fixture ({cols}x{rows})"

    @override
    def get_model_entries(self) -> list[ModelEntry]:
        return [ModelEntry(self.model_path or "")]

    def _pixel_step(self) -> tuple[float, float]:
        cols, rows = self._pixel_matrix
        w, h, _d = self._physical_size
        return w / cols, h / rows

    def _pixel_local_center(self, col: int, row: int) -> tuple[float, float]:
        """Return the local mesh ``(x, y)`` coordinate of a pixel centre on the front face."""
        w, h, _d = self._physical_size
        step_x, step_y = self._pixel_step()
        local_x = -w * 0.5 + (col + 0.5) * step_x
        # Row 0 sits at the top: y starts at +h/2 and decreases as row increases.
        local_y = h * 0.5 - (row + 0.5) * step_y
        return local_x, local_y

    def _object_rotation_matrix(self) -> QMatrix4x4:
        m = QMatrix4x4()
        rot = self.rotation
        m.rotate(rot[2], 0.0, 0.0, 1.0)
        m.rotate(rot[1], 0.0, 1.0, 0.0)
        m.rotate(rot[0], 1.0, 0.0, 0.0)
        return m

    @property
    def lense_colors(self) -> list[LenseLight]:
        """One :class:`LenseLight` billboard per pixel, positioned on the front face."""
        cols, rows = self._pixel_matrix
        step_x, step_y = self._pixel_step()
        scale = float(self.scale)
        size = min(step_x, step_y) * _LENSE_SIZE_FRACTION * scale

        # Recompute the same tangent/bitangent basis Stage3DWidget uses so we
        # can express each pixel's world-space offset (from the fixture centre)
        # in that basis via a dot-product. This keeps pixels attached to the
        # rotated front face for any object rotation.
        rot_mat = self._object_rotation_matrix()
        fwd = rot_mat.map(PixelFixture.beam_local_direction)
        length = fwd.length()
        if length < 1e-6:
            fwd = QVector3D(0.0, 0.0, 1.0)
        else:
            fwd /= length
        world_up = QVector3D(0.0, 0.0, 1.0) if abs(fwd.z()) < 0.999 else QVector3D(0.0, 1.0, 0.0)
        tangent = QVector3D.crossProduct(world_up, fwd)
        if tangent.length() > 1e-6:
            tangent.normalize()
        bitangent = QVector3D.crossProduct(fwd, tangent)

        lights: list[LenseLight] = []
        for row in range(rows):
            for col in range(cols):
                idx = row * cols + col
                lx, ly = self._pixel_local_center(col, row)
                world_offset = rot_mat.map(QVector3D(lx, ly, 0.0)) * scale
                a = QVector3D.dotProduct(world_offset, tangent)
                b = QVector3D.dotProduct(world_offset, bitangent)
                c = QVector3D.dotProduct(world_offset, fwd)
                color = self._pixel_colors[idx] if idx < len(self._pixel_colors) else (0, 0, 0)
                lights.append(
                    LenseLight(
                        position=QVector3D(a, b, c),
                        rotation=QVector3D(0.0, 0.0, 0.0),
                        size=size,
                        color=color,
                        origin_node="",
                        tilt_node="",
                    )
                )
        return lights

    def get_procedural_mesh_data(self) -> tuple[np.ndarray, np.ndarray]:
        """Build a cuboid housing with a recessed pocket per pixel.

        Returns:
            ``(vertex_data, indices)`` — interleaved ``[pos, normal]`` floats
            plus a uint32 triangle index buffer, ready for :meth:`Model3D.upload_mesh`.

        """
        cols, rows = self._pixel_matrix
        w, h, d = self._physical_size
        step_x, step_y = self._pixel_step()

        recess_depth = min(d * _RECESS_FRACTION, min(step_x, step_y) * 0.4)
        bezel = min(step_x, step_y) * _BEZEL_FRACTION
        inner_x = max(1e-4, step_x * 0.5 - bezel)
        inner_y = max(1e-4, step_y * 0.5 - bezel)

        verts: list[float] = []
        idx: list[int] = []

        def add_quad(
            p0: tuple[float, float, float],
            p1: tuple[float, float, float],
            p2: tuple[float, float, float],
            p3: tuple[float, float, float],
            normal: tuple[float, float, float],
        ) -> None:
            """Append a quad as two triangles (CCW winding when viewed against the normal)."""
            base = len(verts) // 6
            for p in (p0, p1, p2, p3):
                verts.extend([p[0], p[1], p[2], normal[0], normal[1], normal[2]])
            idx.extend([base, base + 1, base + 2, base, base + 2, base + 3])

        half_w = w * 0.5
        half_h = h * 0.5
        back_z = -d
        front_normal = (0.0, 0.0, 1.0)

        # Back face (normal -Z)
        add_quad(
            (half_w, -half_h, back_z),
            (half_w, half_h, back_z),
            (-half_w, half_h, back_z),
            (-half_w, -half_h, back_z),
            (0.0, 0.0, -1.0),
        )
        # Bottom face (normal -Y)
        add_quad(
            (-half_w, -half_h, back_z),
            (half_w, -half_h, back_z),
            (half_w, -half_h, 0.0),
            (-half_w, -half_h, 0.0),
            (0.0, -1.0, 0.0),
        )
        # Top face (normal +Y)
        add_quad(
            (-half_w, half_h, 0.0),
            (half_w, half_h, 0.0),
            (half_w, half_h, back_z),
            (-half_w, half_h, back_z),
            (0.0, 1.0, 0.0),
        )
        # Left face (normal -X)
        add_quad(
            (-half_w, -half_h, back_z),
            (-half_w, -half_h, 0.0),
            (-half_w, half_h, 0.0),
            (-half_w, half_h, back_z),
            (-1.0, 0.0, 0.0),
        )
        # Right face (normal +X)
        add_quad(
            (half_w, -half_h, back_z),
            (half_w, half_h, back_z),
            (half_w, half_h, 0.0),
            (half_w, -half_h, 0.0),
            (1.0, 0.0, 0.0),
        )

        # Front face bezel + recessed pockets (one per pixel).
        recess_z = -recess_depth
        for row in range(rows):
            for col in range(cols):
                cx, cy = self._pixel_local_center(col, row)
                cell_x_min = cx - step_x * 0.5
                cell_x_max = cx + step_x * 0.5
                cell_y_min = cy - step_y * 0.5
                cell_y_max = cy + step_y * 0.5
                pocket_x_min = cx - inner_x
                pocket_x_max = cx + inner_x
                pocket_y_min = cy - inner_y
                pocket_y_max = cy + inner_y

                # Bezel strips lie on the front face plane (z=0), normal +Z.
                # Bottom strip
                add_quad(
                    (cell_x_min, cell_y_min, 0.0),
                    (cell_x_max, cell_y_min, 0.0),
                    (cell_x_max, pocket_y_min, 0.0),
                    (cell_x_min, pocket_y_min, 0.0),
                    front_normal,
                )
                # Top strip
                add_quad(
                    (cell_x_min, pocket_y_max, 0.0),
                    (cell_x_max, pocket_y_max, 0.0),
                    (cell_x_max, cell_y_max, 0.0),
                    (cell_x_min, cell_y_max, 0.0),
                    front_normal,
                )
                # Left strip
                add_quad(
                    (cell_x_min, pocket_y_min, 0.0),
                    (pocket_x_min, pocket_y_min, 0.0),
                    (pocket_x_min, pocket_y_max, 0.0),
                    (cell_x_min, pocket_y_max, 0.0),
                    front_normal,
                )
                # Right strip
                add_quad(
                    (pocket_x_max, pocket_y_min, 0.0),
                    (cell_x_max, pocket_y_min, 0.0),
                    (cell_x_max, pocket_y_max, 0.0),
                    (pocket_x_max, pocket_y_max, 0.0),
                    front_normal,
                )

                # Recess side walls (each faces into the pocket toward the viewer)
                # -X wall (facing +X)
                add_quad(
                    (pocket_x_min, pocket_y_min, recess_z),
                    (pocket_x_min, pocket_y_max, recess_z),
                    (pocket_x_min, pocket_y_max, 0.0),
                    (pocket_x_min, pocket_y_min, 0.0),
                    (1.0, 0.0, 0.0),
                )
                # +X wall (facing -X)
                add_quad(
                    (pocket_x_max, pocket_y_max, recess_z),
                    (pocket_x_max, pocket_y_min, recess_z),
                    (pocket_x_max, pocket_y_min, 0.0),
                    (pocket_x_max, pocket_y_max, 0.0),
                    (-1.0, 0.0, 0.0),
                )
                # -Y wall (facing +Y)
                add_quad(
                    (pocket_x_max, pocket_y_min, recess_z),
                    (pocket_x_min, pocket_y_min, recess_z),
                    (pocket_x_min, pocket_y_min, 0.0),
                    (pocket_x_max, pocket_y_min, 0.0),
                    (0.0, 1.0, 0.0),
                )
                # +Y wall (facing -Y)
                add_quad(
                    (pocket_x_min, pocket_y_max, recess_z),
                    (pocket_x_max, pocket_y_max, recess_z),
                    (pocket_x_max, pocket_y_max, 0.0),
                    (pocket_x_min, pocket_y_max, 0.0),
                    (0.0, -1.0, 0.0),
                )
                # Recess bottom (facing +Z toward the viewer)
                add_quad(
                    (pocket_x_min, pocket_y_min, recess_z),
                    (pocket_x_max, pocket_y_min, recess_z),
                    (pocket_x_max, pocket_y_max, recess_z),
                    (pocket_x_min, pocket_y_max, recess_z),
                    front_normal,
                )

        vertex_array = np.array(verts, dtype=np.float32).reshape(-1, 6)
        index_array = np.array(idx, dtype=np.uint32)
        return vertex_array, index_array

    @override
    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        cols, rows = self._pixel_matrix
        w, h, d = self._physical_size
        data.update(
            {
                "pixel_matrix": {"cols": cols, "rows": rows},
                "physical_size": {"width": w, "height": h, "depth": d},
            }
        )
        return data

    @classmethod
    def _read_pixel_matrix(cls, data: dict[str, Any], default: tuple[int, int]) -> tuple[int, int]:
        pm = data.get("pixel_matrix")
        if isinstance(pm, dict):
            return int(pm.get("cols", default[0])), int(pm.get("rows", default[1]))
        if isinstance(pm, (list, tuple)) and len(pm) >= 2:
            return int(pm[0]), int(pm[1])
        return default

    @classmethod
    def _read_physical_size(
        cls, data: dict[str, Any], default: tuple[float, float, float]
    ) -> tuple[float, float, float]:
        ps = data.get("physical_size")
        if isinstance(ps, dict):
            return (
                float(ps.get("width", default[0])),
                float(ps.get("height", default[1])),
                float(ps.get("depth", default[2])),
            )
        if isinstance(ps, (list, tuple)) and len(ps) >= 3:
            return float(ps[0]), float(ps[1]), float(ps[2])
        return default

    @classmethod
    def _read_common_transform(
        cls, data: dict[str, Any], default_scale: float
    ) -> tuple[tuple[float, float, float], tuple[float, float, float], float]:
        pos = data.get("position", {}) or {}
        rot = data.get("rotation", {}) or {}
        position = (float(pos.get("x", 0.0)), float(pos.get("y", 0.0)), float(pos.get("z", 0.0)))
        rotation = (float(rot.get("x", 0.0)), float(rot.get("y", 0.0)), float(rot.get("z", 0.0)))
        scale = float(data.get("scale", default_scale))
        return position, rotation, scale
