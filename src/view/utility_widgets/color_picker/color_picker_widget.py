import os.path

import numpy as np
from PySide6.QtCore import Signal
from PySide6.QtOpenGL import QOpenGLFramebufferObject, QOpenGLBuffer, QOpenGLShaderProgram, QOpenGLShader, \
    QOpenGLVertexArrayObject
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QOpenGLFunctions, QSurfaceFormat

from OpenGL import GL

from model import ColorHSI

_COLOR_SELECTION_SURFACE_FRAG_SHADER = QOpenGLShader(QOpenGLShader.Fragment)
_COLOR_SELECTION_SURFACE_FRAG_SHADER.compileSourceFile(os.path.dirname(__file__) + "/color_selection_surface_frag_shader.glsl")
_SIMPLE_VERT_SHADER = QOpenGLShader(QOpenGLShader.Vertex)
_SIMPLE_VERT_SHADER.compileSourceFile(os.path.dirname(__file__) + "/simple_vert_shader.glsl")


class ColorPickerWidget(QOpenGLWidget, QOpenGLFunctions):

    color_changed: Signal = Signal(ColorHSI)
    END_Z_CLIPPING_DISTANCE = 30
    BEGIN_Z_CLIPPING_DISTANCE = 0

    def __init__(self, parent: QWidget | None):
        super().__init__(parent)
        self._gl_program: QOpenGLShaderProgram = None
        self._gl_vbo_color_quad: QOpenGLBuffer = None
        self._gl_vao: QOpenGLVertexArrayObject = None
        self._r: float = 0
        self._g: float = 0
        self._b: float = 0
        self._selection_diagram_coordinates = np.array([
            0, 1,
            0, 0,
            1, 1,
            1, 0
        ], dtype=np.float32)
        self.context().aboutToBeDestroyed.connect(self._cleanup_gl)

    def initializeGL(self):
        super().initializeGL()
        self.initializeOpenGLFunctions()

        format = QSurfaceFormat()
        format.setDepthBufferSize(24)
        format.setStencilBufferSize(8)
        format.setVersion(4, 1)  # 4.1 is still supported on mac os and new enough for GLSL
        format.setProfile(QSurfaceFormat.CoreProfile)
        self.setFormat(format)

        self._gl_program = QOpenGLShaderProgram()
        self._gl_program.create()

        self._gl_vao = QOpenGLVertexArrayObject()
        self._gl_vao.create()
        self._gl_vao.bind()

        self._gl_vbo_color_quad = QOpenGLBuffer()
        self._gl_vbo_color_quad.create()
        self._gl_vbo_color_quad.bind()
        self._gl_vbo_color_quad.allocate(self._selection_diagram_coordinates.nbytes)
        self._gl_vbo_color_quad.write(0, self._selection_diagram_coordinates.data, self._selection_diagram_coordinates.nbytes)
        # TODO set self.glVertexAttribPointer(...) here

        # TODO repeat for controls interface

        self._gl_program.addShader(_COLOR_SELECTION_SURFACE_FRAG_SHADER)
        self._gl_program.addShader(_SIMPLE_VERT_SHADER)
        self._gl_program.bindAttributeLocation("position", 0)
        self._gl_program.bindAttributeLocation("texture_coordinate", 1)
        if not self._gl_program.link():
            raise RuntimeError("Failed to link shaders.")
        self._gl_program.bind()
        self._recalculate_projection()

    def _cleanup_gl(self):
        self.makeCurrent()
        del self._gl_vbo_color_quad
        self._gl_vbo_color_quad = None
        del self._gl_program
        self._gl_program = None
        del self._gl_vao
        self._gl_vao = None
        self.doneCurrent()
        self.context().aboutToBeDestroyed.disconnect(self._cleanup_gl)

    def _recalculate_projection(self):
        """
        This calculates and sets an orthogonal projection matrix as described in
        https://songho.ca/opengl/gl_projectionmatrix.html.
        """
        vert_projection_matricies = self._gl_program.uniformLocation("projection_matrices")
        r = self.width()
        t = self.height()
        f = self.END_Z_CLIPPING_DISTANCE
        n = self.BEGIN_Z_CLIPPING_DISTANCE
        projection_matrix = np.array([
            1 / r, 0, 0, 0,
            0, 1 / t, 0, 0,
            0, 0, -2 / (f - n), -(f + n) / (f - n),
            0, 0, 0, 1
        ], dtype=np.float32)
        self.glUniform1fv(vert_projection_matricies, projection_matrix.size, projection_matrix)

    def paintGL(self):
        super().paintGL()
        self.glClear(GL.GL_COLOR_BUFFER_BIT)
        # TODO theoretically we somehow need to call self.glUseProgram(self._gl_program) here.
        #  But how do we get the pointer from our program?
        self._gl_program.bind()
        self.glDrawArrays(GL.GL_QUADS, 0, int(self._selection_diagram_coordinates.size / 2))
        self._gl_program.release()

    def resizeGL(self, w, h):
        super().resizeGL(w, h)
        self._recalculate_projection()

    def setBackgroundColor(self, r: int, g: int, b: int, a: int):
        """
        :param r: The red value of the new background color, ranging from 0 to 255
        :param g: The green value of the new background color, ranging from 0 to 255
        :param b: The blue value of the new background color, ranging from 0 to 255
        :param a: The alpha value of the new background color, ranging from 0 to 255
        """
        self.makeCurrent()
        self.glClearColor(r / 255, g / 255, b / 255, a / 255)
        self.update()

    @property
    def color(self) -> ColorHSI:
        return ColorHSI.from_rgb(self._r, self._g, self._b)

    @color.setter
    def color(self, new_color: ColorHSI):
        """
        Use this method to set a new color.
        :param new_color: The new color to set
        :warn: This setter may emit the color_changed signal
        """
        r, g, b = new_color.to_rgb()
        if r != self._r or g != self._g or b != self._b:
            self._r = r
            self._g = g
            self._b = b
            self.update()
            self.color_changed.emit(new_color)

