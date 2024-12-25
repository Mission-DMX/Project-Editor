import os.path

from PySide6.QtOpenGL import QOpenGLFramebufferObject, QOpenGLBuffer, QOpenGLShaderProgram, QOpenGLShader
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QOpenGLFunctions


_COLOR_SELECTION_SURFACE_FRAG_SHADER = QOpenGLShader(QOpenGLShader.Fragment)
_COLOR_SELECTION_SURFACE_FRAG_SHADER.compileSourceFile(os.path.dirname(__file__) + "/color_selection_surface_frag_shader.glsl")
_SIMPLE_VERT_SHADER = QOpenGLShader(QOpenGLShader.Vertex)
_SIMPLE_VERT_SHADER.compileSourceFile(os.path.dirname(__file__) + "/simple_vert_shader.glsl")

class ColorPickerWidget(QOpenGLWidget, QOpenGLFunctions):
    def __init__(self, parent: QWidget | None):
        super().__init__(parent)
        self._gl_program: QOpenGLShaderProgram = None
        self._gl_vbo: QOpenGLBuffer = None

    def initializeGL(self):
        super().initializeGL()
        self._gl_program = QOpenGLShaderProgram()
        self._gl_program.create()
        self._gl_vbo = QOpenGLBuffer()
        self._gl_vbo.create()
        self._gl_program.addShader(_COLOR_SELECTION_SURFACE_FRAG_SHADER)
        self._gl_program.addShader(_SIMPLE_VERT_SHADER)
        self._gl_program.link()

    def paintGL(self):
        super().paintGL()
        self.glClear(QOpenGLFramebufferObject.GL_COLOR_BUFFER_BIT)

    def resizeGL(self, w, h):
        super().resizeGL(w, h)

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

