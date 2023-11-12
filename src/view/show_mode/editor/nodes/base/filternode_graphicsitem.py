from PySide6 import QtGui
from PySide6.QtGui import QPainter
from pyqtgraph.flowchart.Node import NodeGraphicsItem

from model import DataType


class FilterNodeGraphicsItem(NodeGraphicsItem):
    """This class provides a custom renderer for filter nodes"""

    _node_type_brush = QtGui.QBrush(QtGui.QColor(0, 0, 0, 128))
    _data_type_brush = QtGui.QBrush(QtGui.QColor(0, 0, 0, 255))

    def __init__(self, node):
        self.terminals = {}
        self.titleOffset = 25 + 10
        self.nodeOffset = 12 + 7
        super().__init__(node)
        from view.show_mode.editor.nodes.type_to_node_dict import type_to_node
        self._node_type_string = type_to_node[self.node.filter.filter_type]

    def updateTerminals(self):
        # TODO remove this method once the PR got accepted
        self.terminals = {}
        inp = self.node.inputs()
        out = self.node.outputs()

        maxNode = max(len(inp), len(out))

        # calculate new height
        newHeight = self.titleOffset + maxNode * self.nodeOffset

        # if current height is not equal to new height, update
        if not self.bounds.height() == newHeight:
            self.bounds.setHeight(newHeight)
            self.update()

        # Populate inputs
        y = self.titleOffset
        for i, t in inp.items():
            item = t.graphicsItem()
            item.setParentItem(self)
            # item.setZValue(self.zValue()+1)
            item.setAnchor(0, y)
            self.terminals[i] = (t, item)
            y += self.nodeOffset

        # Populate inputs
        y = self.titleOffset
        for i, t in out.items():
            item = t.graphicsItem()
            item.setParentItem(self)
            item.setZValue(self.zValue())
            item.setAnchor(self.bounds.width(), y)
            self.terminals[i] = (t, item)
            y += self.nodeOffset
        # TODO end of code to delete

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
        y_inp = self.titleOffset * 4 + 35
        y_outp = self.titleOffset * 4 + 35
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
            terminal_dt_name = str(dt)
            if terminal.isInput():
                p.drawText(5, y_inp, terminal_dt_name)
                y_inp += self.nodeOffset * 4
            else:
                p.drawText(node_width * 4 - 8 * len(terminal_dt_name), y_outp, terminal_dt_name)
                y_outp += self.nodeOffset * 4
        p.restore()
