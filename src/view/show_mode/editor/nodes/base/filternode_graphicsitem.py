from PySide6 import QtGui
from PySide6.QtGui import QPainter
from pyqtgraph.flowchart.Node import NodeGraphicsItem

from model import DataType


class FilterNodeGraphicsItem(NodeGraphicsItem):
    """This class provides a custom renderer for filter nodes"""

    _node_type_brush = QtGui.QBrush(QtGui.QColor(0, 0, 0, 128))
    _data_type_brush = QtGui.QBrush(QtGui.QColor(0, 0, 0, 255))

    def __init__(self, node):
        super().__init__(node)
        self.setTitleOffset(self.titleOffset() + 10)
        self.setTerminalOffset(self.terminalOffset() + 7)
        from view.show_mode.editor.nodes.type_to_node_dict import type_to_node
        self._node_type_string = type_to_node[self.node.filter.filter_type]

    def paint(self, p: QPainter, *args):
        super().paint(p, *args)
        p.save()
        p.setBrush(FilterNodeGraphicsItem._node_type_brush)
        p.scale(0.5, 0.5)
        p.drawText(5, 15, self._node_type_string)
        p.restore()

        p.save()
        p.setBrush(FilterNodeGraphicsItem._data_type_brush)
        p.scale(0.25, 0.25)
        y_inp = self.titleOffset() * 4 + 35
        y_outp = self.titleOffset() * 4 + 35
        node_width = self.bounds.width()
        for terminal_id, terminal_tuple in self.terminals.items():
            terminal, _ = terminal_tuple
            if not self.node.filter:
                return
            if terminal.isInput():
                dt: DataType = self.node.filter.in_data_types.get(terminal.name())
            elif terminal.isOutput():
                dt = self.node.filter.out_data_types.get(terminal.name())
            else:
                raise ValueError("Expected terminal to be either input or output")
            terminal_dt_name = str(dt) + (self.node.channel_hints.get(terminal.name()) or "")
            if terminal.isInput():
                p.drawText(5, y_inp, terminal_dt_name)
                y_inp += self.terminalOffset() * 4
            else:
                p.drawText(node_width * 4 - 8 * len(terminal_dt_name), y_outp, terminal_dt_name)
                y_outp += self.terminalOffset() * 4
        p.restore()
