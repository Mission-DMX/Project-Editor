"""Show-mode color picker widget backed by the chromaticity ``ColorPickerWidget``."""

from typing import override

from PySide6.QtGui import QAction, QColor
from PySide6.QtWidgets import QColorDialog, QHBoxLayout, QListWidget, QPushButton, QToolBar, QVBoxLayout, QWidget

from model import Filter, UIPage, UIWidget
from model.color_hsi import ColorHSI
from view.utility_widgets.color_picker.color_picker_widget import ColorPickerWidget


class ColorSwiftUIWidget(UIWidget):
    """UIWidget that lets the operator pick a color from a chromaticity diagram and store presets."""

    def __init__(self, parent: UIPage, configuration: dict[str, str]) -> None:
        """Initialize the UI widget with its parent page and configuration dict."""
        super().__init__(parent, configuration)
        self._value: ColorHSI = ColorHSI.from_filter_str("")
        if not self.configuration.get("number_of_presets"):
            self.configuration["number_of_presets"] = "0"
        if not self.configuration.get("stored_presets"):
            self.configuration["stored_presets"] = ""
        self._presets: list[ColorHSI] = []
        self._player_widget: QWidget | None = None
        self._config_widget: QWidget | None = None

    @override
    def set_filter(self, f: Filter, i: int) -> None:
        """Bind the widget to a filter and seed the stored color from its initial parameters."""
        if not f:
            return
        super().set_filter(f, i)
        self._value = ColorHSI.from_filter_str(f.initial_parameters.get("value"))

    def generate_update_content(self) -> list[tuple[str, str]]:
        """Return the current color as a filter-formatted (key, value) pair."""
        return [("value", self._value.format_for_filter())]

    def push_value(self, new_value: ColorHSI) -> None:
        """Replace the currently-held color and transmit the update to the show runtime."""
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
            select_button.clicked.connect(lambda _=None, _i=i: self._select_color(_i))
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
        self._presets = color_presets
        w.setLayout(layout)
        return w

    def get_player_widget(self, parent: QWidget | None) -> QWidget:
        """Return a fresh ``ColorPickerWidget`` wired to push picks to the show runtime."""
        if self._player_widget:
            self._player_widget.deleteLater()
        self._player_widget = ColorPickerWidget(parent)
        self._player_widget.color = self._value
        self._player_widget.color_changed.connect(self.push_value)
        return self._player_widget

    def get_configuration_widget(self, parent: QWidget | None) -> QWidget:
        """Return the preset-row widget shown inside the UI-editor configuration surface."""
        if not self._config_widget:
            self._config_widget = self._build_base_widget(parent, False)
        return self._config_widget

    def copy(self, new_parent: "UIPage") -> "UIWidget":
        """Return a deep copy of this widget attached to a different parent UI page."""
        w = ColorSwiftUIWidget(new_parent, self.configuration)
        self.copy_base(w)
        w._value = self._value.copy()
        return w

    def get_config_dialog_widget(self, parent: QWidget) -> QWidget:
        """Return the modal configuration dialog that lets the designer manage presets."""
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
            self.configuration["stored_presets"] += "{}{}".format(";" if self.configuration["stored_presets"] else "",
                                                                  c.format_for_filter())
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
