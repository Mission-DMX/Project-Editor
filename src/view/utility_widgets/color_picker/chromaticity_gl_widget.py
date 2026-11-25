"""OpenGL 4.1 Core chromaticity diagram widget.

Renders the CIE 1931 xy chromaticity horseshoe with:

* per-pixel xy → sRGB conversion at a configurable luminance,
* sRGB gamut triangle overlay,
* spectral locus curve outline,
* a crosshair marker at the current selection.

The widget is deliberately dumb about higher-level color models — it only knows
xy chromaticity and luminance.  The surrounding composite picker owns the
`ColorHSI` ↔ xy conversion.
"""

from __future__ import annotations

import ctypes
import os
from logging import getLogger
from typing import TYPE_CHECKING, override

import numpy as np
from OpenGL import GL as gl  # noqa: N811
from PySide6.QtCore import Qt, Signal
from PySide6.QtOpenGLWidgets import QOpenGLWidget

from utility import resource_path
from view.gl.shaders import delete_shader, load_and_link_shader_from_files
from view.utility_widgets.color_picker import cie_constants as cie

if TYPE_CHECKING:
    from PySide6.QtGui import QMouseEvent
    from PySide6.QtWidgets import QWidget

logger = getLogger(__name__)


class ChromaticityDiagramGLWidget(QOpenGLWidget):
    """OpenGL CIE xy chromaticity diagram with live mouse picking."""

    xy_picked = Signal(float, float)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumSize(360, 360)
        self.setMouseTracking(False)

        self._program: int = 0
        self._vao: int = 0
        self._vbo: int = 0
        self._gl_initialized: bool = False
        self._init_error: str | None = None

        self._uniforms: dict[str, int] = {}

        self._xy: tuple[float, float] = cie.D65_WHITE_XY
        self._luminance: float = 1.0
        self._dragging: bool = False

    # -----------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------

    @property
    def xy(self) -> tuple[float, float]:
        return self._xy

    def set_xy(self, x: float, y: float) -> None:
        self._xy = (float(x), float(y))
        self.update()

    @property
    def luminance(self) -> float:
        return self._luminance

    def set_luminance(self, luminance: float) -> None:
        self._luminance = max(0.0, min(float(luminance), 1.0))
        self.update()

    # -----------------------------------------------------------------
    # OpenGL lifecycle
    # -----------------------------------------------------------------

    @override
    def initializeGL(self) -> None:
        context = self.context()
        if context is None:
            raise RuntimeError("No OpenGL context available in ChromaticityDiagramGLWidget.initializeGL.")
        context.aboutToBeDestroyed.connect(self._cleanup_gl)

        fmt = context.format()
        logger.info(
            "Initializing ColorPicker chromaticity OpenGL %d.%d profile=%s",
            fmt.majorVersion(),
            fmt.minorVersion(),
            fmt.profile(),
        )

        try:
            self._program = load_and_link_shader_from_files(
                resource_path(os.path.join("resources", "shaders", "color_picker_chromaticity.vert")),
                resource_path(os.path.join("resources", "shaders", "color_picker_chromaticity.frag")),
            )
        except (RuntimeError, OSError) as e:
            self._init_error = f"Chromaticity shader failed: {e}"
            logger.error("%s", self._init_error)
            return

        # Full-screen quad: 6 vertices, 4 floats each (pos.xy, aXY).
        # aPos: [-1, 1]² in clip space; aXY: [0, 1]² mapped to chromaticity domain in the shader.
        verts = np.array(
            [
                # pos.x, pos.y,  aXY.x, aXY.y
                -1.0, -1.0,     0.0, 0.0,
                 1.0, -1.0,     1.0, 0.0,
                 1.0,  1.0,     1.0, 1.0,

                -1.0, -1.0,     0.0, 0.0,
                 1.0,  1.0,     1.0, 1.0,
                -1.0,  1.0,     0.0, 1.0,
            ],
            dtype=np.float32,
        )

        self._vao = gl.glGenVertexArrays(1)
        self._vbo = gl.glGenBuffers(1)
        gl.glBindVertexArray(self._vao)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self._vbo)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, verts.nbytes, verts, gl.GL_STATIC_DRAW)

        stride = 4 * 4  # 4 floats per vertex
        gl.glEnableVertexAttribArray(0)
        gl.glVertexAttribPointer(0, 2, gl.GL_FLOAT, gl.GL_FALSE, stride, ctypes.c_void_p(0))
        gl.glEnableVertexAttribArray(1)
        gl.glVertexAttribPointer(1, 2, gl.GL_FLOAT, gl.GL_FALSE, stride, ctypes.c_void_p(2 * 4))

        gl.glBindVertexArray(0)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)

        for name in (
            "uY",
            "uCursorXY",
            "uPixelPerXYUnit",
            "uBackground",
            "uLocusCount",
            "uLocus",
            "uGamut",
            "uDomain",
        ):
            self._uniforms[name] = gl.glGetUniformLocation(self._program, name)

        self._upload_static_uniforms()
        self._gl_initialized = True

    def _upload_static_uniforms(self) -> None:
        gl.glUseProgram(self._program)

        locus = np.array(cie.SPECTRAL_LOCUS_XY, dtype=np.float32)
        count = locus.shape[0]
        if self._uniforms["uLocus"] >= 0:
            gl.glUniform2fv(self._uniforms["uLocus"], count, locus.flatten())
        if self._uniforms["uLocusCount"] >= 0:
            gl.glUniform1i(self._uniforms["uLocusCount"], count)

        gamut = np.array(cie.SRGB_PRIMARIES_XY, dtype=np.float32).flatten()
        if self._uniforms["uGamut"] >= 0:
            gl.glUniform2fv(self._uniforms["uGamut"], 3, gamut)

        if self._uniforms["uDomain"] >= 0:
            gl.glUniform2f(self._uniforms["uDomain"], cie.XY_DOMAIN_X, cie.XY_DOMAIN_Y)

        if self._uniforms["uBackground"] >= 0:
            gl.glUniform3f(self._uniforms["uBackground"], 0.08, 0.08, 0.09)

        gl.glUseProgram(0)

    def _cleanup_gl(self) -> None:
        self.makeCurrent()
        if self._vbo:
            gl.glDeleteBuffers(1, [self._vbo])
            self._vbo = 0
        if self._vao:
            gl.glDeleteVertexArrays(1, [self._vao])
            self._vao = 0
        if self._program:
            delete_shader(self._program)
            self._program = 0
        self._gl_initialized = False
        self.doneCurrent()
        try:
            self.context().aboutToBeDestroyed.disconnect(self._cleanup_gl)
        except RuntimeError:
            pass

    @override
    def paintGL(self) -> None:
        if not self._gl_initialized:
            # Clear to the background color so we don't flash arbitrary gpu memory.
            gl.glClearColor(0.08, 0.08, 0.09, 1.0)
            gl.glClear(gl.GL_COLOR_BUFFER_BIT)
            return

        gl.glClearColor(0.08, 0.08, 0.09, 1.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

        gl.glUseProgram(self._program)
        if self._uniforms["uY"] >= 0:
            gl.glUniform1f(self._uniforms["uY"], self._luminance)
        if self._uniforms["uCursorXY"] >= 0:
            gl.glUniform2f(self._uniforms["uCursorXY"], self._xy[0], self._xy[1])
        if self._uniforms["uPixelPerXYUnit"] >= 0:
            # Pick the smaller axis so AA doesn't get stretched on non-square widgets.
            pix_per_unit_x = self.width() / cie.XY_DOMAIN_X
            pix_per_unit_y = self.height() / cie.XY_DOMAIN_Y
            gl.glUniform1f(self._uniforms["uPixelPerXYUnit"], min(pix_per_unit_x, pix_per_unit_y))

        gl.glBindVertexArray(self._vao)
        gl.glDrawArrays(gl.GL_TRIANGLES, 0, 6)
        gl.glBindVertexArray(0)
        gl.glUseProgram(0)

    @override
    def resizeGL(self, w: int, h: int) -> None:
        gl.glViewport(0, 0, max(1, w), max(1, h))

    # -----------------------------------------------------------------
    # Mouse interaction
    # -----------------------------------------------------------------

    def _pixel_to_xy(self, px: float, py: float) -> tuple[float, float]:
        if self.width() <= 0 or self.height() <= 0:
            return self._xy
        u = max(0.0, min(px / self.width(), 1.0))
        # Qt origin is top-left; shader xy maps bottom-left as y=0.
        v = max(0.0, min(1.0 - py / self.height(), 1.0))
        return u * cie.XY_DOMAIN_X, v * cie.XY_DOMAIN_Y

    def _update_from_pixel(self, px: float, py: float) -> None:
        x, y = self._pixel_to_xy(px, py)
        if not cie.is_in_spectral_locus(x, y):
            x, y = cie.snap_to_locus(x, y)
        self._xy = (x, y)
        self.xy_picked.emit(x, y)
        self.update()

    @override
    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            pos = event.position()
            self._update_from_pixel(pos.x(), pos.y())
            event.accept()
        else:
            super().mousePressEvent(event)

    @override
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._dragging:
            pos = event.position()
            self._update_from_pixel(pos.x(), pos.y())
            event.accept()
        else:
            super().mouseMoveEvent(event)

    @override
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._dragging:
            self._dragging = False
            event.accept()
        else:
            super().mouseReleaseEvent(event)
