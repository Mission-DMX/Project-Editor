from logging import getLogger
from typing import override

from PySide6.QtCore import QPoint, QSize, Qt, Signal
from PySide6.QtGui import QCloseEvent, QMouseEvent
from PySide6.QtWidgets import QDialog, QLabel, QPushButton, QVBoxLayout, QWidget

from model import UIWidget
from view.show_mode.editor.node_editor_widgets import NodeEditorFilterConfigWidget

logger = getLogger(__name__)


class UIWidgetHolder(QWidget):
    """Widget to hold node editor widgets and move them around"""

    closing = Signal()

    def __init__(self, child: UIWidget, parent: QWidget, instance_for_editor: bool = True) -> None:
        super().__init__(parent)
        self._model: UIWidget = child
        if instance_for_editor:
            self._child = child.get_configuration_widget(self)
        else:
            self._child = child.get_player_widget(self)
            self._child.setEnabled(True)
            self._child.setVisible(True)
        self._child.setParent(self)
        self._label = QLabel(str(child), self)
        self.update_size()
        if instance_for_editor:
            self._close_button = QPushButton("X", self)
            self._close_button.resize(30, 30)
            self._close_button.move(self.width() - 40, 0)
            self._close_button.clicked.connect(self.close)
            self._edit_button = QPushButton("Edit", self)
            self._edit_button.resize(50, 30)
            self._edit_button.move(0, 0)
            self._edit_button.clicked.connect(self._show_edit_dialog)
        self._old_pos = QPoint()
        if instance_for_editor:
            self.setStyleSheet("border: 1px solid black")
        self._instance_for_editor: bool = instance_for_editor
        self.setVisible(True)
        super().move(self._model.position[0], self._model.position[1])
        self._edit_dialog = None

    def update_size(self) -> None:
        self.setMinimumWidth(100)
        self.setMinimumHeight(30)

        child_layout = self._child.layout()
        minimum_size = child_layout.minimumSize() if child_layout else QSize(250, 100)
        w = max(minimum_size.width() + 50, self.minimumWidth())
        h = max(minimum_size.height() + 50, self.minimumHeight())
        self._label.resize(w, 20)
        self._label.move(10, w - 30)
        self.resize(w, h)
        self.repaint()

    @override
    def closeEvent(self, event:QCloseEvent) -> None:
        """Emits closing signal.

        Args:
            event: The closing event.
        """
        self.closing.emit()
        try:
            self._model.parent.widgets.remove(self._model)
        except ValueError:
            pass
        super().closeEvent(event)

    @override
    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Saves the current position on left click.

        Args:
            event: The mouse event.
        """
        if event.button() is Qt.MouseButton.LeftButton and self._instance_for_editor:
            self._old_pos = event.globalPos()

    @override
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Moves the widget on mouse drag.

        Args:
            event: The mouse event.
        """
        super().mouseMoveEvent(event)
        if not self._instance_for_editor:
            return
        # offset = QPoint(event.globalPos() - self._old_pos)
        self.move(self.parent().mapFromGlobal(event.globalPos()))
        # self.move(self.x() + offset.x(), self.y() + offset.y())
        self._old_pos = event.globalPos()

    @property
    def holding(self) -> NodeEditorFilterConfigWidget:
        """The widget the holder is holding"""
        return self._child

    @property
    def widget(self) -> UIWidget:
        return self._model

    def move(self, new_pos: QPoint) -> None:
        super().move(new_pos)
        self._model.position = (new_pos.x(), new_pos.y())

    def _show_edit_dialog(self) -> None:
        if not self._edit_dialog:
            self._edit_dialog = QDialog(self)
            layout = QVBoxLayout()
            layout.addWidget(self._model.get_config_dialog_widget(self._edit_dialog))
            # TODO add cancel and close buttons
            self._edit_dialog.setLayout(layout)
        self._edit_dialog.show()

    def unregister(self) -> None:
        """Clean up the stored widget and remove it from the parent canvas."""
        # setting the parent to None is required!
        try:
            self._child.setParent(None)
            self._child.setVisible(False)
            self._child.setEnabled(False)
        except RuntimeError as e:
            logger.exception("BUG! This widget is already deleted: %s", e)
