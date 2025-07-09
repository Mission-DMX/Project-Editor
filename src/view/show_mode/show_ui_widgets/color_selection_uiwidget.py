from PySide6.QtGui import QAction, QColor
from PySide6.QtWidgets import (
    QColorDialog,
    QDialog,
    QHBoxLayout,
    QListWidget,
    QPushButton,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from model import ColorHSI, Filter, UIPage, UIWidget


class ColorSelectionUIWidget(UIWidget):

    def __init__(self, parent: UIPage, configuration: dict[str, str]) -> None:
        super().__init__(parent, configuration)

        self._value: ColorHSI = ColorHSI.from_filter_str("")
        if not self.configuration.get("number_of_presets"):
            self.configuration["number_of_presets"] = "0"
        if not self.configuration.get("stored_presets"):
            self.configuration["stored_presets"] = ""
        self._presets: list[ColorHSI] = []
        self._player_widget: QWidget | None = None
        self._config_widget: QWidget | None = None
        self._filter = None

    def set_filter(self, f: Filter, i: int) -> None:
        if not f:
            return
        super().set_filter(f, i)
        self._filter = f
        self.associated_filters["constant"] = f.filter_id
        self._value = ColorHSI.from_filter_str(f.initial_parameters.get("value"))

    def generate_update_content(self) -> list[tuple[str, str]]:
        return [("value", self._value.format_for_filter())]

    def push_value(self, new_value: ColorHSI) -> None:
        self._value = new_value
        self.push_update()

    def _build_base_widget(self, parent: QWidget, for_player: bool) -> QWidget:
        w = QWidget(parent)
        layout = QHBoxLayout()
        color_presets_str = self.configuration.get("stored_presets")
        if color_presets_str:
            color_presets = color_presets_str.split(";")
            color_preset_length = len(color_presets)
            for i in range(color_preset_length):
                color_presets[i] = ColorHSI.from_filter_str(color_presets[i])
        else:
            color_presets = []
            color_preset_length = 0
        for i in range(int(self.configuration.get("number_of_presets"))):
            column_layout = QVBoxLayout()
            select_button = QPushButton("Sel", w)
            select_button.setEnabled(for_player)
            select_button.clicked.connect(lambda _i=i: self._select_color(_i))
            column_layout.addWidget(select_button)
            color_label = QWidget(w)
            color_label.setMinimumWidth(16)
            color_label.setMinimumHeight(16)
            color_label.setAutoFillBackground(True)
            if i < color_preset_length:
                c = color_presets[i]
            else:
                c = ColorHSI(25.0, 0.5, 0.5)
                self._presets.append(c)
            p = color_label.palette()
            p.setColor(color_label.backgroundRole(), c.to_qt_color())
            color_label.setPalette(p)
            column_layout.addWidget(color_label)
            transmit_button = QPushButton("Set", w)
            transmit_button.setEnabled(for_player)
            transmit_button.clicked.connect(lambda _i=i: self.push_value(self._presets[_i]))
            column_layout.addWidget(transmit_button)
            layout.addLayout(column_layout)
        self._presets: list[ColorHSI] = color_presets
        w.setLayout(layout)
        return w

    def get_player_widget(self, parent: QWidget | None) -> QWidget:
        if self._player_widget:
            self._player_widget.deleteLater()
        self._player_widget = self._build_base_widget(parent, True)
        return self._player_widget

    def get_configuration_widget(self, parent: QWidget | None) -> QWidget:
        if not self._config_widget:
            self._config_widget = self._build_base_widget(parent, False)
        return self._config_widget

    def copy(self, new_parent: UIPage) -> UIWidget:
        w = ColorSelectionUIWidget(new_parent, self.configuration)
        self.copy_base(w)
        w.set_filter(self._filter, 0)
        w._value = self._value.copy()
        return w

    def get_config_dialog_widget(self, parent: QDialog) -> QWidget:
        w = QWidget(parent)
        layout = QVBoxLayout()
        toolbar = QToolBar(w)
        add_action = QAction("Add Preset", toolbar)
        toolbar.addAction(add_action)
        layout.addWidget(toolbar)
        preset_list = QListWidget(w)
        layout.addWidget(preset_list)
        w.setLayout(layout)

        def _add_preset(c_template: QColor) -> None:
            c: ColorHSI = ColorHSI.from_qt_color(c_template)
            self._presets.append(c)
            self.configuration["number_of_presets"] = str(int(self.configuration["number_of_presets"]) + 1)
            self.configuration[
                "stored_presets"] += f"{";" if self.configuration["stored_presets"] else ''}{c.format_for_filter()}"
            preset_list.addItem(c.format_for_filter())
            # TODO add buttons to existing widgets in a smarter way
            if self._player_widget:
                player_parent = self._player_widget.parent()
                self._player_widget = self._build_base_widget(player_parent, True)
            if self._config_widget:
                config_parent = self._config_widget.parent()
                self._config_widget = self._build_base_widget(config_parent, False)

        def open_dialog() -> None:
            d = QColorDialog(w)
            d.colorSelected.connect(_add_preset)
            d.show()

        add_action.triggered.connect(open_dialog)
        return w

    def _select_color(self, i: int) -> None:
        if not self._player_widget:
            return
        d = QColorDialog(self._player_widget)
        d.colorSelected.connect(lambda color: self._set_preset(i, color))
        d.show()

    def _set_preset(self, i: int, color: QColor) -> None:
        self._presets[i] = ColorHSI.from_qt_color(color)
