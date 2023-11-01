from PySide6 import QtGui
from PySide6.QtGui import QPainter
from pyqtgraph.flowchart import Terminal
from pyqtgraph.flowchart.Terminal import TerminalGraphicsItem

from model import DataType


class TerminalTypeGraphicsItem(TerminalGraphicsItem):

    def __init__(self, term: Terminal, dt: DataType, parent=None):
        super().__init__(term, parent=parent)
        self._dt: DataType = dt
        self._data_type_brush = QtGui.QBrush(QtGui.QColor(0, 0, 0, 128))

    def paint(self, p: QPainter, *args):
        super().paint(p, *args)
