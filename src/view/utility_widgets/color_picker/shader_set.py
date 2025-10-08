import os.path

from OpenGL import GL as gl

_CACHE_DIR = ""

def _check_shader_cache():
    global _CACHE_DIR
    _CACHE_DIR = "/var/cache/shaders/missionDMX/shaders"
    # TODO create cache directory if it does not exist. If this fails, log an error and go to /tmp
    # TODO check version.txt of directory. If file exist and does not match editor version, erase all content of directory
    # TODO if file does not exist now, create it and write the version of the editor into it


class ShaderSet:
    """A custom class providing shader services as the Qt6 ones are broken."""

    def __init__(self, vertex_shader_source_name: str, fragment_shader_source_name: str) -> None:
        self._vertex_shader_source_name = vertex_shader_source_name
        self._fragment_shader_source_name = fragment_shader_source_name
        self._shader_program_ptr: int = 0
        self._vertex_shader_ptr: int = 0
        self._fragment_shader_ptr: int = 0

    def on_gl_init(self):
        binary_format = 0  # TODO find out correct one
        self._shader_program_ptr = gl.glCreateProgram()
        # TODO compile shaders into cache if they do not exist.
        with open(_CACHE_DIR + os.path.sep + self._vertex_shader_source_name + ".bin", "rb") as f:
            vertex_binary = f.read()
        self._vertex_shader_ptr = gl.glCreateShader(gl.GL_VERTEX_SHADER)
        gl.glShaderBinary(1, self._vertex_shader_ptr, binary_format, vertex_binary, len(vertex_binary))

        # TODO attach shaders, link program and perform glGetprogramiv finally delete shaders

_check_shader_cache()
