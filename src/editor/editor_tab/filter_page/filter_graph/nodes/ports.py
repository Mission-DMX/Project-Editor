from NodeGraphQt.base.model import PortDatatypeModel
from PySide6 import QtCore, QtGui


def draw_square_port(painter: QtGui.QPainter, rect: QtCore.QRectF, info: dict) -> None:
    """
    Custom paint function for drawing a Square shaped port.

    Args:
        painter: painter object.
        rect: port rect used to describe parameters needed to draw.
        info: information describing the ports current state.
            {
                'port_type': 'in',
                'color': (0, 0, 0),
                'border_color': (255, 255, 255),
                'multi_connection': False,
                'connected': False,
                'hovered': False,
            }

    """
    painter.save()

    # mouse over port color.
    if info["hovered"]:
        color = QtGui.QColor(14, 45, 59)
        border_color = QtGui.QColor(136, 255, 35, 255)
    # port connected color.
    elif info["connected"]:
        color = QtGui.QColor(195, 60, 60)
        border_color = QtGui.QColor(200, 130, 70)
    # default port color
    else:
        color = QtGui.QColor(*info["color"])
        border_color = QtGui.QColor(*info["border_color"])

    pen = QtGui.QPen(border_color, 1.8)
    pen.setJoinStyle(QtCore.Qt.PenJoinStyle.MiterJoin)

    painter.setPen(pen)
    painter.setBrush(color)
    painter.drawRect(rect)

    painter.restore()


def draw_triangle_port(painter, rect, info):
    """
    Custom paint function for drawing a Triangle shaped port.

    Args:
        painter: painter object.
        rect: port rect used to describe parameters needed to draw.
        info: information describing the ports current state.
            {
                'port_type': 'in',
                'color': (0, 0, 0),
                'border_color': (255, 255, 255),
                'multi_connection': False,
                'connected': False,
                'hovered': False,
            }

    """

    painter.save()

    # create triangle polygon.

    size = int(rect.height() / 2)

    triangle = QtGui.QPolygonF()

    triangle.append(QtCore.QPointF(-size, size))

    triangle.append(QtCore.QPointF(0.0, -size))

    triangle.append(QtCore.QPointF(size, size))

    # map polygon to port position.

    transform = QtGui.QTransform()

    transform.translate(rect.center().x(), rect.center().y())

    port_poly = transform.map(triangle)

    # mouse over port color.

    if info["hovered"]:
        color = QtGui.QColor(14, 45, 59)

        border_color = QtGui.QColor(136, 255, 35)

    # port connected color.

    elif info["connected"]:
        color = QtGui.QColor(195, 60, 60)

        border_color = QtGui.QColor(200, 130, 70)

    # default port color

    else:
        color = QtGui.QColor(*info["color"])

        border_color = QtGui.QColor(*info["border_color"])

    pen = QtGui.QPen(border_color, 1.8)

    pen.setJoinStyle(QtCore.Qt.MiterJoin)

    painter.setPen(pen)

    painter.setBrush(color)

    painter.drawPolygon(port_poly)

    painter.restore()


BIT_8_PORT = PortDatatypeModel("8bit", (0, 200, 0), draw_square_port)
BIT_16_PORT = PortDatatypeModel("16bit", (200, 0, 0), draw_square_port)

DOUBLE_PORT = PortDatatypeModel("float", (0, 200, 0), draw_triangle_port)

COLOR_PORT = PortDatatypeModel("color", (200, 0, 0))
BOOL_PORT = PortDatatypeModel("bool", (0, 200, 0))
TIME_PORT = PortDatatypeModel("time", (0, 200, 200))

PORT_NAMES: dict[str, PortDatatypeModel] = {
    BIT_8_PORT.name: BIT_8_PORT,
    BIT_16_PORT.name: BIT_16_PORT,
    DOUBLE_PORT.name: DOUBLE_PORT,
    COLOR_PORT.name: COLOR_PORT,
    BOOL_PORT.name: BOOL_PORT
}
