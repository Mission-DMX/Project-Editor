from PySide6 import QtGui
from PySide6.QtGui import QPainter
from pyqtgraph.flowchart import Terminal
from pyqtgraph.flowchart.Terminal import TerminalGraphicsItem

from model import DataType, Filter


class TerminalTypeGraphicsItem(TerminalGraphicsItem):

    def __init__(self, term: Terminal, f: Filter, parent=None):
        super().__init__(term, parent=parent)
        self._filter: Filter = f
        self._data_type_brush = QtGui.QBrush(QtGui.QColor(0, 0, 0, 128))

    def paint(self, p: QPainter, *args):
        super().paint(p, *args)
        if not self._filter:
            return
        if self.term.isInput():
            dt: DataType = self._filter.in_data_types.get(self.term.name())
        elif self.term.isOutput():
            dt = self._filter.out_data_types.get(self.term.name())
        else:
            raise ValueError("Expected terminal to be either input or output")
        tname = str(dt.name)
        p.save()
        p.setBrush(self._data_type_brush)
        p.scale(0.25, 0.25)
        pos = self.label.pos()
        if self.term.isInput():
            p.drawText(pos.x() + 5, pos.y() + 5 + 25, tname)
        else:
            p.drawText(pos.x() - 5, pos.y() + 5 + 25, tname)
        p.restore()
