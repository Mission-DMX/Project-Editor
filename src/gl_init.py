"""Contains OpenGL context initialization."""

from logging import getLogger

from PySide6.QtGui import QSurfaceFormat

logger = getLogger(__name__)


def opengl_context_init() -> None:
    """Initialize the default OpenGL surface format used by all QOpenGLWidget-based windows.

    Warning: Do not request a fixed version/profile here (e.g. 4.1 core). Requesting a specific
    version in the *default* format makes context creation fail with EGL_BAD_MATCH on some
    EGL/NVIDIA driver stacks as soon as a QOpenGLWidget is shown, which leaves the whole window
    invisible. Without a version request the driver-provided default context (desktop GL,
    compatibility profile) is used, which still supports the 4.1 core GLSL shaders used by the
    stage visualizer.
    """
    fmt = QSurfaceFormat()
    fmt.setDepthBufferSize(24)
    fmt.setStencilBufferSize(8)

    QSurfaceFormat.setDefaultFormat(fmt)
    logger.debug("Initialized default OpenGL surface format")
