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


def upload_mesh(vertex_data: np.ndarray, indices: np.ndarray) -> Model3D:
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
    return Model3D(vao, vbo, ebo, int(indices.size))
