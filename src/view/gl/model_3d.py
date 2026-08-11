"""Contains Model3D binding and mesh upload functions."""

from __future__ import annotations

import ctypes
from logging import getLogger
from typing import TYPE_CHECKING

import numpy as np
from OpenGL import GL as gl  # NOQA: N811 it is common practice to import is as lower case gl. Also it's not a const.

if TYPE_CHECKING:
    from PySide6.QtGui import QOpenGLContext

logger = getLogger(__name__)

class Model3D:
    """GPU mesh: VAO + VBO + EBO + index count.

    Class only contains bindings. Data must be loaded separately.

    """

    def __init__(self, vao: int, vbo: int, ebo: int, index_count: int) -> None:
        """Initialize struct."""
        self.vao: int = vao
        self.vbo: int = vbo
        self.ebo: int = ebo
        self.index_count: int = index_count
        self._still_bound: bool = True

    def unload(self) -> None:
        """Release the VAO, VBO and EBO that belong to this model.

        After this call the instance is considered “unbound”; any further
        attempts to use it will raise because the GPU resources are gone.
        """
        if not self._still_bound:
            return
        gl.glDeleteBuffers(1, np.array([self.vbo], dtype=np.uint32))
        gl.glDeleteBuffers(1, np.array([self.ebo], dtype=np.uint32))
        gl.glDeleteVertexArrays(1, np.array([self.vao], dtype=np.uint32))

        self._still_bound = False
        self.vao = self.vbo = self.ebo = 0

    def __del__(self) -> None:
        """Checks if the object was successfully deleted or throws an error.

        This cannot happen automatically as it must occur within the thread and OpenGL context that created the model.

        """
        if self._still_bound:
            try:
                self.unload()
            except gl.GLError as e:
                raise RuntimeError("Model3D object is still bound. This would cause a memory leak.") from e

    @classmethod
    def upload_mesh(cls, vertex_data: np.ndarray, indices: np.ndarray,
                    context: QOpenGLContext | None = None) -> Model3D:
        """Upload interleaved position+normal vertex data to the GPU.

        Vertex layout: [pos_x, pos_y, pos_z, norm_x, norm_y, norm_z] (6 floats).
        Returns a Model3D with the GPU handles.
        """
        if context is None:
            logger.warning("Context was None. Make sure the mesh data is uploaded from the correct context.")
        vertex_data = np.ascontiguousarray(vertex_data, dtype=np.float32)
        indices = np.ascontiguousarray(indices, dtype=np.uint32)
        ebo, vao, vbo = cls._allocate_vao(indices, vertex_data)
        stride = 6 * 4  # 6 floats * 4 bytes
        gl.glVertexAttribPointer(0, 3, gl.GL_FLOAT, gl.GL_FALSE, stride, ctypes.c_void_p(0))
        gl.glEnableVertexAttribArray(0)
        gl.glVertexAttribPointer(1, 3, gl.GL_FLOAT, gl.GL_FALSE, stride, ctypes.c_void_p(12))
        gl.glEnableVertexAttribArray(1)
        gl.glBindVertexArray(0)
        return cls(vao, vbo, ebo, int(indices.size))

    @classmethod
    def upload_vao(cls, verts: np.ndarray, indices: np.ndarray, context: QOpenGLContext | None = None, stride: int = 24,
                   vertex_size: int = 3, vertex_location_index: int = 0, uv_location_index: int = 1) -> Model3D:
        """Upload interleaved position+normal vertex data to a new VAO."""
        if context is None:
            logger.warning("Context was None. Make sure the VAO is uploaded from the correct context.")
        ebo, vao, vbo = cls._allocate_vao(indices, verts)
        gl.glVertexAttribPointer(vertex_location_index, vertex_size, gl.GL_FLOAT, gl.GL_FALSE, stride,
                                 ctypes.c_void_p(0))
        gl.glEnableVertexAttribArray(vertex_location_index)
        sizeof_float = 4
        gl.glVertexAttribPointer(uv_location_index, vertex_size, gl.GL_FLOAT, gl.GL_FALSE, stride,
                                 ctypes.c_void_p(vertex_size * sizeof_float))
        gl.glEnableVertexAttribArray(uv_location_index)
        gl.glBindVertexArray(0)
        return cls(vao, vbo, ebo, int(indices.size))

    @classmethod
    def _allocate_vao(cls, indices: np.ndarray, verts: np.ndarray) -> tuple[int, int, int]:
        vao = gl.glGenVertexArrays(1)
        vbo = gl.glGenBuffers(1)
        ebo = gl.glGenBuffers(1)
        gl.glBindVertexArray(vao)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vbo)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, verts.nbytes, verts, gl.GL_STATIC_DRAW)
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, ebo)
        gl.glBufferData(gl.GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, gl.GL_STATIC_DRAW)
        return ebo, vao, vbo
