"""Contains shader loading methods."""

from __future__ import annotations

from typing import TYPE_CHECKING

from OpenGL import GL as gl  # NOQA: N811 it is common practice to import is as lower case gl. Also it's not a const.

if TYPE_CHECKING:
    from OpenGL.constant import IntConstant


def _compile_shader(src: bytes, stype: IntConstant) -> int:
    """Compile a single GLSL shader and raise on error."""
    s = gl.glCreateShader(stype)
    gl.glShaderSource(s, src)
    gl.glCompileShader(s)
    if gl.glGetShaderiv(s, gl.GL_COMPILE_STATUS) != gl.GL_TRUE:
        log = gl.glGetShaderInfoLog(s)
        kind = "vertex" if stype == gl.GL_VERTEX_SHADER else "fragment"
        raise RuntimeError(f"{kind} shader failed: {log}")
    return s


def load_and_link_shader(vs_src: bytes, fs_src: bytes) -> int:
    """Compile vertex + fragment shaders and link into a program."""
    vs = _compile_shader(vs_src, gl.GL_VERTEX_SHADER)
    fs = _compile_shader(fs_src, gl.GL_FRAGMENT_SHADER)
    prog = gl.glCreateProgram()
    gl.glAttachShader(prog, vs)
    gl.glAttachShader(prog, fs)
    gl.glLinkProgram(prog)
    if gl.glGetProgramiv(prog, gl.GL_LINK_STATUS) != gl.GL_TRUE:
        raise RuntimeError(f"link failed: {gl.glGetProgramInfoLog(prog)}")
    gl.glDeleteShader(vs)
    gl.glDeleteShader(fs)
    return prog

def load_and_link_shader_from_files(vertex_shader_path: str, fragment_shader_path: str) -> int:
    """Compile vertex + fragment shaders from file and link into a program."""
    with open(vertex_shader_path, "rb") as f:
        vertex_bytes: bytes = f.read()
    with open(fragment_shader_path, "rb") as f:
        fragment_bytes: bytes = f.read()
    return load_and_link_shader(vertex_bytes, fragment_bytes)
