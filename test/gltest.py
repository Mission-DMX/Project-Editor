import numpy as np
from OpenGL import GL
from PySide6 import QtWidgets
from PySide6.QtCore import Qt
from PySide6.QtGui import QSurfaceFormat, QMatrix4x4
from PySide6.QtOpenGL import QOpenGLShaderProgram, QOpenGLBuffer, QOpenGLShader
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtWidgets import QVBoxLayout, QWidget

from style import Style


class GLTestWidget(QOpenGLWidget):
    def __init__(self, parent: QWidget | None):
        super().__init__(parent)
        self._gl_program: QOpenGLShaderProgram | None = None
        self._gl_vbo_color_quad: int = 0
        self.setMinimumHeight(600)
        self.setMinimumWidth(600)
        self._gpu_cords_array = 0
        self._cpu_cords_array = np.array([
            0.1, 0.9,  # top left  # 0 ~= -1
            0.9, 0.9,  # top right
            0.1, 0.1,  # bottom left
            0.1, 0.9,  # top left
            0.9, 0.1,  # bottom right
            0.1, 0.1  # bottom left
        ], dtype=np.float32)
        self._cpu_indicies = np.array([0, 1, 2, 3, 4, 5], dtype=np.int32)
        self._gpu_indicies = 0
        self._initialized = False

    def resizeGL(self, w, h, /):
        super().resizeGL(w, h)
        print("Resize called.")

    def initializeGL(self):
        print("Initializing GL...")
        f = self.context().functions()
        f.initializeOpenGLFunctions()
        print(
            f"GL version: {self.context().format().majorVersion()}.{self.context().format().minorVersion()} {'valid' if self.context().isValid() else 'invalid'}")
        print("Vendor: ", GL.glGetString(GL.GL_VENDOR), " renderer: ", GL.glGetString(GL.GL_RENDERER), " max version: ",
              GL.glGetString(GL.GL_VERSION), " GLSL Version: ", GL.glGetString(GL.GL_SHADING_LANGUAGE_VERSION))
        GL.glClearColor(0.0, 0.0, 0.50, 1)
        GL.glViewport(0, 0, self.width(), self.height())
        print("Errors prior to compile shaders: ", GL.glGetError())
        self._allocate_quad()
        print("Buffers allocated.")
        self._compile_shaders()
        self._initialized = True
        print("Done.")

    def _allocate_quad(self):
        buf = np.array([0], dtype=np.int32)
        print("Errors prior to buffer: ", GL.glGetError())
        GL.glGenVertexArrays(1, buf.data)
        self._vao_id = buf[0]
        GL.glBindVertexArray(self._vao_id)

        GL.glGenBuffers(1, buf.data)
        self._gpu_indicies = buf[0]
        GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, self._gpu_indicies)
        GL.glBufferData(GL.GL_ELEMENT_ARRAY_BUFFER, self._cpu_indicies.nbytes, self._cpu_indicies.data,
                        GL.GL_STATIC_DRAW)

        GL.glGenBuffers(1, buf.data)
        self._gpu_cords_array = buf[0]
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self._gpu_cords_array)
        GL.glBufferData(GL.GL_ARRAY_BUFFER, self._cpu_cords_array.nbytes, self._cpu_cords_array.data, GL.GL_STATIC_DRAW)
        GL.glVertexAttribPointer(0, 2, GL.GL_FLOAT, GL.GL_FALSE, 0, 0)
        GL.glEnableVertexAttribArray(0)
        GL.glBindVertexArray(0)
        print("Buffer write errors: ", GL.glGetError())

    def _compile_shaders(self):
        self._gl_program = QOpenGLShaderProgram()
        self._gl_program.create()
        self._frag_shader = QOpenGLShader(QOpenGLShader.ShaderTypeBit.Fragment)
        if not self._frag_shader.compileSourceCode("""
        #version 410 core

        layout(location = 0) out vec4 fragColor;

        void main() {
            vec2 position = gl_FragCoord.ab;
            if (mod(position.x, 2) == 0) {
                discard;
            }
            fragColor.rga = vec3(1.0);
            fragColor.b = mod(position.x, 2);
        }
        """):
            print("Failed to compile fragment shader: ", self._frag_shader.log())
        else:
            print("Successfully compiled fragment shader.")

        self._vert_shader = QOpenGLShader(QOpenGLShader.ShaderTypeBit.Vertex)
        if not self._vert_shader.compileSourceCode("""
        #version 410 core

        layout(location = 0) in vec2 position;

        uniform mat4 modelView;
        uniform mat4 projection;

        void main() {
            gl_Position = projection * modelView * vec4(position.xy, 0.00, 1.0);
        }
        """):
            print("Failed to compile vertex shader:", self._vert_shader.log())
        else:
            print("Successfully compiled vertex shader.")

        self._gl_program.addShader(self._frag_shader)
        self._gl_program.addShader(self._vert_shader)
        self._gl_program.bindAttributeLocation("position", 0)
        if not self._gl_program.link():
            raise RuntimeError(
                "Failed to link shaders:" + self._gl_program.log()
            )
        else:
            print("Successfully linked test GL program.")
        if not self._gl_program.bind():
            print("Failed to bind GL program.")
        print("Bind Error: ", GL.glGetError(), self._gl_program.log())
        m = QMatrix4x4()
        print("Is Identity: ", m.isIdentity())
        self._gl_program.setUniformValue("modelView", m)
        m.ortho(0, 1, 0, 1, 0, -1)
        self._gl_program.setUniformValue("projection", m)
        self._gl_program.release()

    def paintGL(self):
        if not self._initialized:
            print("Not initialized yet.")
            return
        else:
            print("Drawing")
        print("Binding VAO ", self._vao_id)
        GL.glBindVertexArray(self._vao_id)
        GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, self._gpu_indicies)
        print(self._gl_program.bind())
        # GL.glDrawElements(GL.GL_TRIANGLES, 6, GL.GL_UNSIGNED_INT, 0)
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, 6)
        print("E1: ", GL.glGetError())
        self._gl_program.release()
        GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, 0)
        GL.glBindVertexArray(0)
        print("E2: ", GL.glGetError())


if __name__ == "__main__":
    fmt = QSurfaceFormat()
    fmt.setDepthBufferSize(24)
    fmt.setStencilBufferSize(8)
    fmt.setVersion(4, 1)  # Request OpenGL 4.1 compatible context
    fmt.setProfile(QSurfaceFormat.CoreProfile)

    QSurfaceFormat.setDefaultFormat(fmt)
    QtWidgets.QApplication.setAttribute(
        Qt.ApplicationAttribute.AA_UseDesktopOpenGL
    )
    app = QtWidgets.QApplication([])
    app.setStyleSheet(Style.APP)
    window = QtWidgets.QMainWindow()
    layout = QVBoxLayout()
    widget = GLTestWidget(window)
    layout.addWidget(widget)
    window.setLayout(layout)
    window.showMaximized()
    app.exec()