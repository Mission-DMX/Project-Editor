from PySide6 import QtGui
from PySide6.QtCore import QPoint
from PySide6.QtGui import QPainter
from pyqtgraph.flowchart.Node import NodeGraphicsItem

from model import DataType
from view.show_mode.editor.nodes.base.terminal_type_graphics_item import TerminalTypeGraphicsItem


class FilterNodeGraphicsItem(NodeGraphicsItem):
    """This class provides a custom renderer for filter nodes"""

    def __init__(self, node):
        self.terminals = {}
        self.titleOffset = 25 + 10
        self.nodeOffset = 12 + 7
        super().__init__(node)
        from view.show_mode.editor.nodes.type_to_node_dict import type_to_node
        self._node_type_string = type_to_node[self.node.filter.filter_type]
        self._node_type_brush = QtGui.QBrush(QtGui.QColor(0, 0, 0, 128))

    def updateTerminals(self):
        for terminal_index in self.terminals.keys():
            terminal, terminal_graphics_item = self.terminals[terminal_index]
            if isinstance(terminal.graphicsItem(), TerminalTypeGraphicsItem):
                continue
            if terminal.isInput():
                dt: DataType = self.node.filter.in_data_types.get(terminal_index)
            elif terminal.isOutput():
                dt = self.node.filter.out_data_types.get(terminal_index)
            else:
                raise ValueError("Expected terminal to be either input or output")
            terminal._graphicsItem = TerminalTypeGraphicsItem(terminal, dt, self)

        # TODO uncomment to this, once PR got accepted.
        #super().updateTerminals()
        # TODO delete this once PR got accepted
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
        p.setBrush(self._node_type_brush)
        p.scale(0.5, 0.5)
        p.drawText(5, 15, self._node_type_string)
        p.restore()
