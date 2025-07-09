
from logging import getLogger

from PySide6.QtGui import QSurfaceFormat

logger = getLogger(__file__)


def opengl_context_init() -> None:
    fmt = QSurfaceFormat()
    fmt.setDepthBufferSize(24)
    fmt.setStencilBufferSize(8)
    fmt.setVersion(4, 1)  # Request OpenGL 4.1 compatible context
    fmt.setProfile(QSurfaceFormat.CoreProfile)

    QSurfaceFormat.setDefaultFormat(fmt)
    logger.debug("Initialized OpenGL context to 4.1")
