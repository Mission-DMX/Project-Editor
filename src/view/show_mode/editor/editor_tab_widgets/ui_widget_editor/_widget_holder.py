from PySide6.QtCore import Signal, QPoint, QSize
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QWidget, QLabel, QPushButton, QDialog, QVBoxLayout

from model import UIWidget
from view.show_mode.editor.node_editor_widgets import NodeEditorFilterConfigWidget


class UIWidgetHolder(QWidget):
    """Widget to hold node editor widgets and move them around"""

    closing = Signal()

    def __init__(self, child: UIWidget, parent: QWidget, instance_for_editor: bool = True):
        super().__init__(parent)
        self._model: UIWidget = child
        if instance_for_editor:
            self._child = child.get_configuration_widget(self)
        else:
            self._child = child.get_player_widget(self)
            self._child.setEnabled(True)
            self._child.setVisible(True)
        self._child.setParent(self)
        self._label = QLabel(child.filter_id, self)
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
        self.setVisible(True)
        super().move(self._model.position[0], self._model.position[1])
        self._edit_dialog = None

    def update_size(self):
        self.setMinimumWidth(100)
        self.setMinimumHeight(30)

        child_layout = self._child.layout()
        if child_layout:
            minimum_size = child_layout.totalMinimumSize()
        else:
            minimum_size = QSize(250, 100)
        w = max(minimum_size.width() + 50, self.minimumWidth())
        h = max(minimum_size.height() + 50, self.minimumHeight())
        self._label.resize(w, 20)
        self._label.move(10, w - 30)
        self.resize(w, h)
        self.repaint()

    def closeEvent(self, event) -> None:
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

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Saves the current position on left click.

        Args:
            event: The mouse event.
        """
        if event.button() is Qt.MouseButton.LeftButton:
            self._old_pos = event.globalPos()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Moves the widget on mouse drag.

        Args:
            event: The mouse event.
        """
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

    def move(self, new_pos: QPoint):
        super().move(new_pos)
        self._model.position = (new_pos.x(), new_pos.y())

    def _show_edit_dialog(self):
        if not self._edit_dialog:
            self._edit_dialog = QDialog(self)
            layout = QVBoxLayout()
            layout.addWidget(self._model.get_config_dialog_widget(self._edit_dialog))
            # TODO add cancel and close buttons
            self._edit_dialog.setLayout(layout)
        self._edit_dialog.show()

    def unregister(self):
        # setting the parent to None is required!
        self._child.setParent(None)
        self._child.setVisible(False)
        self._child.setEnabled(False)