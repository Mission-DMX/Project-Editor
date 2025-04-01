import os.path
from logging import getLogger

import numpy as np
from OpenGL import GL
from PySide6.QtCore import Signal
from PySide6.QtGui import QOpenGLExtraFunctions, QOpenGLFunctions, QSurfaceFormat
from PySide6.QtOpenGL import (QOpenGLBuffer, QOpenGLFramebufferObject, QOpenGLShader, QOpenGLShaderProgram,
                              QOpenGLVertexArrayObject)
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtWidgets import QWidget

from model.color_hsi import ColorHSI

logger = getLogger(__file__)


class ColorPickerWidget(QOpenGLWidget):

    color_changed: Signal = Signal(ColorHSI)
    END_Z_CLIPPING_DISTANCE = 30
    BEGIN_Z_CLIPPING_DISTANCE = 0

    _COLOR_SELECTION_SURFACE_FRAG_SHADER: QOpenGLShader | None = None
    _SIMPLE_VERT_SHADER: QOpenGLShader | None = None

    def __init__(self, parent: QWidget | None):
        super().__init__(parent)
        self._gl_program: QOpenGLShaderProgram = None
        self._gl_vbo_color_quad: QOpenGLBuffer = None
        self._gl_vao: QOpenGLVertexArrayObject = None
        self._r: float = 0
        self._g: float = 0
        self._b: float = 0
        frame_scale = 100
        self._selection_diagram_coordinates = np.array([
            0, 1 * frame_scale,
            0, 0,
            1 * frame_scale, 1 * frame_scale,
            1 * frame_scale, 0
        ], dtype=np.float32)

        self.setMinimumHeight(800)
        self.setMinimumWidth(600)
        # FIXME due to yet unknown reasons we cannot set the dimensions after the constructor finished.

    def initializeGL(self):
        super().initializeGL()
        context = self.context()
        if context is not None:
            context.aboutToBeDestroyed.connect(self._cleanup_gl)
        else:
            raise Exception("There must be an OpenGL context by now.")
        f = context.functions()
        f.initializeOpenGLFunctions()

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

        if ColorPickerWidget._COLOR_SELECTION_SURFACE_FRAG_SHADER is None:
            shader_source = os.path.dirname(__file__) + "/color_selection_surface_frag_shader.glsl"
            ColorPickerWidget._COLOR_SELECTION_SURFACE_FRAG_SHADER = QOpenGLShader(QOpenGLShader.ShaderTypeBit.Fragment)
            if not ColorPickerWidget._COLOR_SELECTION_SURFACE_FRAG_SHADER.compileSourceFile(shader_source):
                logger.error("Failed to compile fragment shader.\nSource file: %s\nLog: %s\n",
                             ColorPickerWidget._COLOR_SELECTION_SURFACE_FRAG_SHADER.log(), shader_source)
            else:
                logger.debug("Successfully compiled fragment shader from %s.", shader_source)

        if ColorPickerWidget._SIMPLE_VERT_SHADER is None:
            ColorPickerWidget._SIMPLE_VERT_SHADER = QOpenGLShader(QOpenGLShader.ShaderTypeBit.Vertex)
            shader_source = os.path.dirname(__file__) + "/simple_vert_shader.glsl"
            if not ColorPickerWidget._SIMPLE_VERT_SHADER.compileSourceFile(shader_source):
                logger.error("Failed to compile vertex shader.\nSource File: %s\nLog: %s\n",
                             ColorPickerWidget._SIMPLE_VERT_SHADER.log(), shader_source)
            else:
                logger.debug("Successfully compiled vertex shader from %s.", shader_source)

        self._gl_program.addShader(ColorPickerWidget._COLOR_SELECTION_SURFACE_FRAG_SHADER)
        self._gl_program.addShader(ColorPickerWidget._SIMPLE_VERT_SHADER)
        self._gl_program.bindAttributeLocation("position", 0)
        self._gl_program.bindAttributeLocation("texture_coordinate", 1)
        if not self._gl_program.link():
            raise RuntimeError("Failed to link shaders. Log={}".format(self._gl_program.log()))
        else:
            logger.debug("Successfully linked GL program")
        self._gl_program.bind()
        self.setBackgroundColor(5, 5, 5, 255)
        self.set_cursor_position((10, 10), (self.width(), self.height()))
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
        self.makeCurrent()
        vert_projection_matrix = self._gl_program.uniformLocation("projectionMatrix")
        vert_model_matrix = self._gl_program.uniformLocation("modelMatrix")
        r = self.width()
        t = self.height()
        f = self.END_Z_CLIPPING_DISTANCE
        n = self.BEGIN_Z_CLIPPING_DISTANCE
        projection_matrix = np.array([
            1.0 / r, 0.0, 0.0, 0.0,
            0.0, 1.0 / t, 0.0, 0.0,
            0.0, 0.0, -2.0 / (f - n), -(f + n) / (f - n),
            0.0, 0.0, 0.0, 1.0
        ], dtype=np.float32)
        model_matrix = np.array([
            1.0, 0.0, 0.0, 0.0,
            0.0, 1.0, 0.0, 0.0,
            0.0, 0.0, 1.0, 0.0,
            0.0, 0.0, 0.0, 1.0
        ], dtype=np.float32)
        f = self.context().functions()
        f.glUniformMatrix4fv(vert_projection_matrix, 1, 0, projection_matrix)
        f.glUniformMatrix4fv(vert_model_matrix, 1, 0, model_matrix)
        self.doneCurrent()

    def set_cursor_position(self, cursor: tuple[int, int], cord_size: tuple[int, int]):
        self.makeCurrent()
        cursor_url = self._gl_program.uniformLocation("in_cursor_position")
        cord_size_url = self._gl_program.uniformLocation("in_cord_size")
        f = self.context().functions()
        f.glUniform2i(cursor_url, cursor[0], cursor[1])
        f.glUniform2i(cord_size_url, cord_size[0], cord_size[1])
        self.doneCurrent()

    def paintGL(self):
        super().paintGL()
        f = self.context().functions()
        f.glClear(GL.GL_COLOR_BUFFER_BIT)
        # TODO theoretically we somehow need to call self.glUseProgram(self._gl_program) here.
        #  But how do we get the pointer from our program?
        self._gl_program.bind()
        f.glDrawArrays(GL.GL_QUADS, 0, int(self._selection_diagram_coordinates.size / 2))
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
        f = self.context().functions()
        f.glClearColor(r / 255, g / 255, b / 255, a / 255)
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

