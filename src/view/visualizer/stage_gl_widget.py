import logging, ctypes
from PySide6 import QtGui
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from OpenGL import GL as gl

logger = logging.getLogger(__file__)


class Model3D:
    def __init__(self, vao, vbo, ebo, index_count):
        self.vao = vao
        self.vbo = vbo
        self.ebo = ebo
        self.index_count = index_count


class Stage3DWidget(QOpenGLWidget):

    def __init__(self, stage_config, parent=None):
        super().__init__(parent)
        self._stage_config = stage_config
        self._shader_program = None
        # Uniform-Locations
        self._proj_matrix_loc = None
        self._view_matrix_loc = None
        self._model_matrix_loc = None
        self._light_pos_loc = None
        self._view_pos_loc = None
        # Camera
        self._camera_pos = QtGui.QVector3D(0.0, 200.0, 400.0)
        self._camera_target = QtGui.QVector3D(0.0, 0.0, 0.0)
        self._camera_up = QtGui.QVector3D(0.0, 1.0, 0.0)
        # Model Buffer
        self._models: dict[str, Model3D] = {}

    def initializeGL(self):

        gl.glClearColor(0.1, 0.1, 0.1, 1.0)
        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glEnable(gl.GL_CULL_FACE)
        gl.glCullFace(gl.GL_BACK)

        vertex_shader_source = b"""
        #version 410 core
        layout(location = 0) in vec3 aPosition;
        layout(location = 1) in vec3 aNormal;
        uniform mat4 model;
        uniform mat4 view;
        uniform mat4 projection;
        out vec3 Normal;
        out vec3 FragPos;
        void main() {
            FragPos = vec3(model * vec4(aPosition, 1.0));
            Normal = mat3(transpose(inverse(model))) * aNormal;
            gl_Position = projection * view * vec4(FragPos, 1.0);
        }
        """
        fragment_shader_source = b"""
        #version 410 core
        in vec3 Normal;
        in vec3 FragPos;
        uniform vec3 lightPos;
        uniform vec3 viewPos;
        out vec4 FragColor;
        void main() {
            vec3 color = vec3(0.7, 0.7, 0.8);
            vec3 norm = normalize(Normal);
            vec3 lightDir = normalize(lightPos - FragPos);
            float diff = max(dot(norm, lightDir), 0.0);
            vec3 diffuse = diff * vec3(1.0);
            vec3 ambient = vec3(0.2);
            vec3 result = (ambient + diffuse) * color;
            FragColor = vec4(result, 1.0);
        }
        """
        # Compile shaders
        vs = gl.glCreateShader(gl.GL_VERTEX_SHADER)
        gl.glShaderSource(vs, vertex_shader_source)
        gl.glCompileShader(vs)
        if gl.glGetShaderiv(vs, gl.GL_COMPILE_STATUS) != gl.GL_TRUE:
            log = gl.glGetShaderInfoLog(vs)
            logger.error("Vertex shader compilation failed: %s", log)
        fs = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)
        gl.glShaderSource(fs, fragment_shader_source)
        gl.glCompileShader(fs)
        if gl.glGetShaderiv(fs, gl.GL_COMPILE_STATUS) != gl.GL_TRUE:
            log = gl.glGetShaderInfoLog(fs)
            logger.error("Fragment shader compilation failed: %s", log)

        self._shader_program = gl.glCreateProgram()
        gl.glAttachShader(self._shader_program, vs)
        gl.glAttachShader(self._shader_program, fs)
        gl.glLinkProgram(self._shader_program)
        if gl.glGetProgramiv(self._shader_program, gl.GL_LINK_STATUS) != gl.GL_TRUE:
            log = gl.glGetProgramInfoLog(self._shader_program)
            logger.error("Shader program linking failed: %s", log)

        gl.glDeleteShader(vs)
        gl.glDeleteShader(fs)

        self._proj_matrix_loc = gl.glGetUniformLocation(self._shader_program, b"projection")
        self._view_matrix_loc = gl.glGetUniformLocation(self._shader_program, b"view")
        self._model_matrix_loc = gl.glGetUniformLocation(self._shader_program, b"model")
        self._light_pos_loc = gl.glGetUniformLocation(self._shader_program, b"lightPos")
        self._view_pos_loc = gl.glGetUniformLocation(self._shader_program, b"viewPos")

        for obj in self._stage_config.objects:
            self._ensure_model_loaded(obj)

    def resizeGL(self, width, height):

        aspect = width / height if height != 0 else 1.0
        projection = QtGui.QMatrix4x4()
        projection.perspective(45.0, aspect, 0.1, 10000.0)
        gl.glViewport(0, 0, width, height)

        gl.glUseProgram(self._shader_program)
        proj_data = projection.copyDataTo()

        gl.glUniformMatrix4fv(self._proj_matrix_loc, 1, gl.GL_TRUE, proj_data)
        gl.glUseProgram(0)

        self._projection_matrix = projection

    def paintGL(self):
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        gl.glUseProgram(self._shader_program)

        view = QtGui.QMatrix4x4()
        view.lookAt(self._camera_pos, self._camera_target, self._camera_up)
        view_data = view.copyDataTo()
        gl.glUniformMatrix4fv(self._view_matrix_loc, 1, gl.GL_TRUE, view_data)

        cam = self._camera_pos
        gl.glUniform3f(self._view_pos_loc, cam.x(), cam.y(), cam.z())
        gl.glUniform3f(self._light_pos_loc, cam.x(), cam.y(), cam.z())

        # Drawing all objects
        for obj in self._stage_config.objects:

            model = QtGui.QMatrix4x4()
            model.translate(obj.position[0], obj.position[1], obj.position[2])
            model.rotate(obj.rotation[2], 0.0, 0.0, 1.0)  # Z-Rotation
            model.rotate(obj.rotation[1], 0.0, 1.0, 0.0)  # Y-Rotation
            model.rotate(obj.rotation[0], 1.0, 0.0, 0.0)  # X-Rotation
            model_data = model.copyDataTo()
            gl.glUniformMatrix4fv(self._model_matrix_loc, 1, gl.GL_TRUE, model_data)

            # Binding VAO
            if obj.model_path in self._models:
                m = self._models[obj.model_path]
                gl.glBindVertexArray(m.vao)
                gl.glDrawElements(gl.GL_TRIANGLES, m.index_count, gl.GL_UNSIGNED_INT, None)
        gl.glBindVertexArray(0)
        gl.glUseProgram(0)

    def _ensure_model_loaded(self, obj):
        path = obj.model_path
        if path in self._models:
            return
        try:
            vertices = []
            normals = []
            faces = []
            # .obj file parse
            with open(path, 'r', encoding='UTF-8') as f:
                for line in f:
                    if line.startswith('v '):
                        parts = line.strip().split()
                        if len(parts) >= 4:
                            vertices.append((float(parts[1]), float(parts[2]), float(parts[3])))
                    elif line.startswith('vn '):
                        parts = line.strip().split()
                        if len(parts) >= 4:
                            normals.append((float(parts[1]), float(parts[2]), float(parts[3])))
                    elif line.startswith('f '):
                        parts = line.strip().split()[1:]
                        face = []
                        for part in parts:
                            indices = part.split('/')
                            vi = int(indices[0])
                            ni = int(indices[-1]) if indices[-1] != '' else None
                            face.append((vi, ni))
                        faces.append(face)
            vertex_data = []
            indices = []
            index_map = {}
            for face in faces:
                # Triangulate faces if more than 3 vertices
                if len(face) < 3:
                    continue
                if len(face) == 3:
                    tri_vertices = face
                else:
                    for k in range(1, len(face) - 1):
                        tri_vertices = [face[0], face[k], face[k + 1]]
                        for (vi, ni) in tri_vertices:
                            key = (vi, ni)
                            if key not in index_map:
                                pos = vertices[vi - 1]
                                if ni is not None and ni <= len(normals):
                                    norm = normals[ni - 1]
                                else:
                                    norm = (0.0, 1.0, 0.0)
                                idx = len(index_map)
                                index_map[key] = idx
                                vertex_data.extend([pos[0], pos[1], pos[2], norm[0], norm[1], norm[2]])
                            indices.append(index_map[key])
                    continue

                for (vi, ni) in tri_vertices:
                    key = (vi, ni)
                    if key not in index_map:
                        pos = vertices[vi - 1]
                        if ni is not None and ni <= len(normals):
                            norm = normals[ni - 1]
                        else:
                            norm = (0.0, 1.0, 0.0)
                        idx = len(index_map)
                        index_map[key] = idx
                        vertex_data.extend([pos[0], pos[1], pos[2], norm[0], norm[1], norm[2]])
                    indices.append(index_map[key])


            vertex_data = (gl.GLfloat * len(vertex_data))(*vertex_data)
            index_array = (gl.GLuint * len(indices))(*indices)

            vao = gl.glGenVertexArrays(1)
            vbo = gl.glGenBuffers(1)
            ebo = gl.glGenBuffers(1)

            gl.glBindVertexArray(vao)
            gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vbo)
            gl.glBufferData(gl.GL_ARRAY_BUFFER, len(vertex_data) * 4, vertex_data, gl.GL_STATIC_DRAW)
            gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, ebo)
            gl.glBufferData(gl.GL_ELEMENT_ARRAY_BUFFER, len(index_array) * 4, index_array, gl.GL_STATIC_DRAW)

            gl.glVertexAttribPointer(0, 3, gl.GL_FLOAT, gl.GL_FALSE, 6 * 4, ctypes.c_void_p(0))
            gl.glEnableVertexAttribArray(0)
            gl.glVertexAttribPointer(1, 3, gl.GL_FLOAT, gl.GL_FALSE, 6 * 4, ctypes.c_void_p(12))
            gl.glEnableVertexAttribArray(1)
            gl.glBindVertexArray(0)

            model_data = Model3D(vao, vbo, ebo, len(indices))
            self._models[path] = model_data
            logger.info("Loaded model %s (vertices: %d, indices: %d)", path, len(vertices), len(indices))
        except Exception as e:
            logger.error("Error loading model from %s: %s", path, e)

    def load_object(self, obj):
        self._ensure_model_loaded(obj)

    def remove_object(self, obj):
        path = obj.model_path
        # Check if another object still uses the model
        still_used = False
        for other in self._stage_config.objects:
            if other.model_path == path:
                still_used = True
                break
        if not still_used and path in self._models:
            model = self._models[path]
            gl.glDeleteBuffers(1, [model.vbo])
            gl.glDeleteBuffers(1, [model.ebo])
            gl.glDeleteVertexArrays(1, [model.vao])
            del self._models[path]
            logger.info("Unloaded model %s from GPU", path)
