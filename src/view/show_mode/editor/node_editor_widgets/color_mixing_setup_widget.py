# coding=utf-8
from PySide6.QtGui import QBrush, QColor, QPainter, QPaintEvent
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QSpinBox, QVBoxLayout, QWidget

from controller.utils.yaml import yaml_load
from model import Filter
from view.show_mode.editor.node_editor_widgets import NodeEditorFilterConfigWidget


class _ColorHelpWidget(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent=parent)
        self.setMinimumWidth(30 * 4)
        self.setMinimumHeight(25 * 4)
        self._data: list[dict] = []

    def set_help_content(self, d: list[dict]):
        self._data = d
        self.repaint()

    def paintEvent(self, ev: QPaintEvent):
        w = self.width()
        h = self.height()
        if w == 0 or h == 0:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(0, 0, w, h, QColor.fromRgb(0x3A, 0x3A, 0x3A))
        black_brush = QBrush()
        black_brush.setColor(QColor.fromRgb(0, 0, 0))
        painter.setBrush(black_brush)
        y = 0
        for example in self._data:
            x = 0
            for cinput in example.get("inputs"):
                if x > 0:
                    painter.drawText(x - 6, y + 17, "+")
                painter.drawRect(x + 4, y + 4, 17, 17)
                painter.fillRect(x + 5, y + 5, 15, 15, QColor.fromRgb(cinput["r"], cinput["g"], cinput["b"]))
                x += 30
            painter.drawText(x - 6, y + 17, "=")
            painter.drawRect(x + 4, y + 4, 17, 17)
            output = example.get("output")
            painter.fillRect(x + 5, y + 5, 15, 15, QColor.fromRgb(output["r"], output["g"], output["b"]))
            y += 25
        painter.end()


class ColorMixingSetupWidget(NodeEditorFilterConfigWidget):
    _help_data = yaml_load("resources/data/color_mixing.yml")

    def __init__(self, filter_: Filter, parent: QWidget = None):
        super().__init__()
        self._widget = QWidget(parent=parent)
        self._color_help_widget = _ColorHelpWidget(parent=self._widget)
        self._color_help_widget.set_help_content(ColorMixingSetupWidget._help_data["hsv"])
        self._channel_count_spinbox = QSpinBox(parent=self._widget)
        self._channel_count_spinbox.setMinimum(0)
        self._method_selection_box = QComboBox(parent=self._widget)
        self._method_selection_box.currentTextChanged.connect(self._selected_method_changed)
        self._method_selection_box.setEditable(False)
        self._method_selection_box.addItems(ColorMixingSetupWidget._help_data.keys())
        self._method_selection_box.setCurrentText("hsv")

        layout = QVBoxLayout()
        control_layout = QHBoxLayout()
        layout.addLayout(control_layout)
        control_layout.addWidget(self._method_selection_box)
        control_layout.addWidget(self._channel_count_spinbox)
        layout.addWidget(self._color_help_widget)
        self._widget.setLayout(layout)

    def _get_configuration(self) -> dict[str, str]:
        return {
            "input_count": str(self._channel_count_spinbox.value()),
            "method": str(self._method_selection_box.currentText())
        }

    def _load_configuration(self, conf: dict[str, str]):
        try:
            self._channel_count_spinbox.setValue(int(conf.get("input_count")))
        except ValueError:
            self._channel_count_spinbox.setValue(2)
        self._method_selection_box.setCurrentText(conf.get("method"))

    def get_widget(self) -> QWidget:
        return self._widget

    def _load_parameters(self, parameters: dict[str, str]):
        # We're not using UI parameters
        pass

    def _get_parameters(self) -> dict[str, str]:
        return dict()

    def _selected_method_changed(self, new_method: str):
        self._color_help_widget.set_help_content(ColorMixingSetupWidget._help_data.get(new_method))
