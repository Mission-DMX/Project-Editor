from __future__ import annotations

from typing import TYPE_CHECKING

from pyqtgraph.flowchart.Node import NodeGraphicsItem
from PySide6 import QtGui

if TYPE_CHECKING:
    from collections.abc import Callable

    from PySide6.QtGui import QPainter
    from PySide6.QtWidgets import QStyleOptionGraphicsItem, QWidget

    from model import DataType
    from view.show_mode.editor.nodes import FilterNode

class FilterNodeGraphicsItem(NodeGraphicsItem):
    """This class provides a custom renderer for filter nodes"""

    _node_type_brush = QtGui.QBrush(QtGui.QColor(0, 0, 0, 128))
    _data_type_brush = QtGui.QBrush(QtGui.QColor(0, 0, 0, 255))

    def __init__(self, node: FilterNode) -> None:
        super().__init__(node)
        self.setTitleOffset(self.titleOffset() + 10)
        self.setTerminalOffset(self.terminalOffset() + 7)
        self._node_type_string = self.node.nodeName
        self.additional_rendering_method: Callable[[QPainter], None] | None = None

    def paint(self, painter: QPainter, *args: QStyleOptionGraphicsItem | QWidget | None) -> None:
        super().paint(painter, *args)
        painter.save()
        painter.setBrush(FilterNodeGraphicsItem._node_type_brush)
        painter.scale(0.5, 0.5)
        painter.drawText(5, 15, self._node_type_string)
        painter.restore()

        painter.save()
        painter.setBrush(FilterNodeGraphicsItem._data_type_brush)
        painter.scale(0.25, 0.25)
        y_inp = self.titleOffset() * 4 + 35
        y_outp = self.titleOffset() * 4 + 35
        node_width = self.bounds.width()
        for terminal_tuple in self.terminals.values():
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
                painter.drawText(5, y_inp, terminal_dt_name)
                y_inp += self.terminalOffset() * 4
            else:
                painter.drawText(node_width * 4 - 8 * len(terminal_dt_name), y_outp, terminal_dt_name)
                y_outp += self.terminalOffset() * 4
        additional_rendering_method = self.additional_rendering_method
        if additional_rendering_method is not None:
            painter.setBrush(FilterNodeGraphicsItem._data_type_brush)
            additional_rendering_method(painter)
        painter.restore()
