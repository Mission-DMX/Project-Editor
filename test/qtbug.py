import os

import numpy as np
from OpenGL import GL
from PySide6 import QtWidgets
from PySide6.QtCore import Qt
from PySide6.QtGui import QOpenGLFunctions, QSurfaceFormat
from PySide6.QtOpenGL import QOpenGLBuffer, QOpenGLShader, QOpenGLShaderProgram
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtWidgets import QVBoxLayout
from Style import Style

FRAG_SHADER = QOpenGLShader(QOpenGLShader.Fragment)
FRAG_SHADER.compileSourceCode("""
#version 410 core
void main() {gl_FragColor = vec4(1.0, 1.0, 1.0, 1.0);}
""")
_SIMPLE_VERT_SHADER = QOpenGLShader(QOpenGLShader.Vertex)
_SIMPLE_VERT_SHADER.compileSourceCode("""
#version 410 core
in vec2 position;
in vec2 texture_coordinate;

uniform struct {
	mat4 projectionMatrix;
	mat4 modelMatrix;
} projection_matrices;

smooth out vec2 ioVertexTexCoord;

void main() {
    mat4 mvpMatrix = projection_matrices.projectionMatrix * projection_matrices.modelMatrix;
    gl_Position = mvpMatrix * vec4(position, 0.0, 1.0);
    ioVertexTexCoord = texture_coordinate;
}
""")


class TestWidget(QOpenGLWidget):
    END_Z_CLIPPING_DISTANCE = 30
    BEGIN_Z_CLIPPING_DISTANCE = 0

    def __init__(self, parent):
        super().__init__(parent)
        self._gl_program: QOpenGLShaderProgram = None

    def initializeGL(self):
        super().initializeGL()
        context = self.context()
        if context is not None:
            context.aboutToBeDestroyed.connect(self._cleanup_gl)
        else:
            raise Exception("There must be an OpenGL context by now.")
        f = context.functions()
        f.initializeOpenGLFunctions()

        format = QSurfaceFormat()
        format.setDepthBufferSize(24)
        format.setStencilBufferSize(8)
        format.setVersion(4, 1)
        format.setProfile(QSurfaceFormat.CoreProfile)
        self.setFormat(format)

        self._gl_program = QOpenGLShaderProgram()
        self._gl_program.create()
        # TODO set self.glVertexAttribPointer(...) here

        # TODO repeat for controls interface

        self._gl_program.addShader(FRAG_SHADER)
        self._gl_program.addShader(_SIMPLE_VERT_SHADER)

        self._gl_program.bindAttributeLocation("position", 0)
        self._gl_program.bindAttributeLocation("texture_coordinate", 1)
        if not self._gl_program.link():
            raise RuntimeError("Failed to link shaders.")
        self._gl_program.bind()
        self._recalculate_projection()

    def _cleanup_gl(self):
        self.makeCurrent()
        del self._gl_program
        self._gl_program = None
        self.doneCurrent()
        self.context().aboutToBeDestroyed.disconnect(self._cleanup_gl)

    def _recalculate_projection(self):
        """
        This calculates and sets an orthogonal projection matrix
        """
        vert_projection_matrices = self._gl_program.uniformLocation("projection_matrices")
        r = self.width()
        t = self.height()
        f = self.END_Z_CLIPPING_DISTANCE
        n = self.BEGIN_Z_CLIPPING_DISTANCE
        projection_matrix = [
            1.0 / r, 0.0, 0.0, 0.0,
            0.0, 1.0 / t, 0.0, 0.0,
            0.0, 0.0, -2.0 / (f - n), -(f + n) / (f - n),
            0.0, 0.0, 0.0, 1.0
        ]
        f = self.context().functions()
        count = len(projection_matrix)

        # Here are the offending calls
        #f.glUniform1fv(vert_projection_matrices, count, projection_matrix) # Fails
        self._gl_program.setUniformValueArray(vert_projection_matrices, projection_matrix, count) # Fails
        #self._gl_program.setUniformValueArray(vert_projection_matrices, np.array(projection_matrix, dtype=np.float32).data, count) # Fails

    def paintGL(self):
        super().paintGL()
        f = self.context().functions()
        f.glClear(GL.GL_COLOR_BUFFER_BIT)
        self._gl_program.bind()
        # would do something meaningful here
        self._gl_program.release()

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

if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    app.setStyleSheet(Style.APP)
    app.setAttribute(Qt.ApplicationAttribute.AA_UseDesktopOpenGL)
    window = QtWidgets.QMainWindow()
    layout = QVBoxLayout()
    widget = TestWidget(window)
    layout.addWidget(widget)
    window.setLayout(layout)
    window.showMaximized()
    app.exec()
