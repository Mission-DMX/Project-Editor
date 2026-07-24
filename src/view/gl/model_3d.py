"""Contains Model3D binding and mesh upload functions."""

from __future__ import annotations

import ctypes

import numpy as np
from OpenGL import GL as gl  # NOQA: N811 it is common practice to import is as lower case gl. Also it's not a const.


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
        gl.glDeleteBuffers(1, np.array([self.vbo], dtype=np.uint32))
        gl.glDeleteBuffers(1, np.array([self.ebo], dtype=np.uint32))
        gl.glDeleteVertexArrays(1, np.array([self.vao], dtype=np.uint32))

        self._still_bound = False
        self.vao = self.vbo = self.ebo = 0

    def __del__(self) -> None:
        """Checks if the object was successfully deleted or throws an error.

        This cannot happen automatically as it must occur within the thread that created the model.

        """
        if self._still_bound:
            raise RuntimeError("Model3D object is still bound. This would cause a memory leak.")

    @classmethod
    def upload_mesh(cls, vertex_data: np.ndarray, indices: np.ndarray) -> Model3D:
        """Upload interleaved position+normal vertex data to the GPU.

        Vertex layout: [pos_x, pos_y, pos_z, norm_x, norm_y, norm_z] (6 floats).
        Returns a Model3D with the GPU handles.
        """
        vertex_data = np.ascontiguousarray(vertex_data, dtype=np.float32)
        indices = np.ascontiguousarray(indices, dtype=np.uint32)
        vao = gl.glGenVertexArrays(1)
        vbo = gl.glGenBuffers(1)
        ebo = gl.glGenBuffers(1)
        gl.glBindVertexArray(vao)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vbo)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, vertex_data.nbytes, vertex_data, gl.GL_STATIC_DRAW)
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, ebo)
        gl.glBufferData(gl.GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, gl.GL_STATIC_DRAW)
        stride = 6 * 4  # 6 floats * 4 bytes
        gl.glVertexAttribPointer(0, 3, gl.GL_FLOAT, gl.GL_FALSE, stride, ctypes.c_void_p(0))
        gl.glEnableVertexAttribArray(0)
        gl.glVertexAttribPointer(1, 3, gl.GL_FLOAT, gl.GL_FALSE, stride, ctypes.c_void_p(12))
        gl.glEnableVertexAttribArray(1)
        gl.glBindVertexArray(0)
        return cls(vao, vbo, ebo, int(indices.size))

    @classmethod
    def upload_vao(cls, verts: np.ndarray, indices: np.ndarray) -> Model3D:
        """Upload interleaved position+normal vertex data to a new VAO."""
        vao = gl.glGenVertexArrays(1)
        vbo = gl.glGenBuffers(1)
        ebo = gl.glGenBuffers(1)
        gl.glBindVertexArray(vao)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vbo)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, verts.nbytes, verts, gl.GL_STATIC_DRAW)
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, ebo)
        gl.glBufferData(gl.GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, gl.GL_STATIC_DRAW)
        gl.glVertexAttribPointer(0, 3, gl.GL_FLOAT, gl.GL_FALSE, 24, ctypes.c_void_p(0))
        gl.glEnableVertexAttribArray(0)
        gl.glVertexAttribPointer(1, 3, gl.GL_FLOAT, gl.GL_FALSE, 24, ctypes.c_void_p(12))
        gl.glEnableVertexAttribArray(1)
        gl.glBindVertexArray(0)
        return cls(vao, vbo, ebo, int(indices.size))
