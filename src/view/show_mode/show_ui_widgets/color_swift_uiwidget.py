"""Show-mode color picker widget backed by the chromaticity ``ColorPickerWidget``."""

from typing import override

from PySide6.QtGui import QAction, QColor
from PySide6.QtWidgets import QColorDialog, QHBoxLayout, QListWidget, QPushButton, QToolBar, QVBoxLayout, QWidget

from model import Filter, UIPage, UIWidget
from model.color_hsi import ColorHSI
from view.utility_widgets.color_picker.color_picker_widget import ColorPickerWidget


class ColorSwiftUIWidget(UIWidget):
    """UIWidget that lets the operator pick a color from a chromaticity diagram and store presets."""

    _DEFAULT_PRESET = ColorHSI(25.0, 0.5, 0.5)

    def __init__(self, parent: UIPage, configuration: dict[str, str]) -> None:
        """Initialize the UI widget with its parent page and configuration dict."""
        super().__init__(parent, configuration)
        self._value: ColorHSI = ColorHSI.from_filter_str("")
        if not self.configuration.get("number_of_presets"):
            self.configuration["number_of_presets"] = "0"
        if not self.configuration.get("stored_presets"):
            self.configuration["stored_presets"] = ""
        self._presets: list[ColorHSI] = []
        # The player surface is the chromaticity picker; the preset-row widget is
        # only built for the editor's configuration surface (and the modal preset
        # management dialog).  Separating them avoids the "preset row clobbers
        # the picker" bug.
        self._player_picker_widget: ColorPickerWidget | None = None
        self._config_preset_row_widget: QWidget | None = None
        self._dialog_preset_list: QListWidget | None = None

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

    # -----------------------------------------------------------------
    # Preset serialization
    # -----------------------------------------------------------------

    def _serialize_presets(self) -> None:
        """Mirror ``self._presets`` back into the configuration dict so save/reload persists them."""
        self.configuration["number_of_presets"] = str(len(self._presets))
        self.configuration["stored_presets"] = ";".join(p.format_for_filter() for p in self._presets)

    def _rebuild_preset_views(self) -> None:
        """Rebuild the editor's preset-row widget so swatches reflect ``self._presets``."""
        if self._config_preset_row_widget:
            config_parent = self._config_preset_row_widget.parent()
            self._config_preset_row_widget = self._build_base_widget(config_parent, for_player=False)

    # -----------------------------------------------------------------
    # Composite widget builders
    # -----------------------------------------------------------------

    def _build_base_widget(self, parent: QWidget, for_player: bool) -> QWidget:
        w = QWidget(parent)
        layout = QHBoxLayout()
        color_presets_str = self.configuration.get("stored_presets")
        if color_presets_str:
            color_presets: list[ColorHSI] = [ColorHSI.from_filter_str(s) for s in color_presets_str.split(";")]
        else:
            color_presets = []
        stored_preset_count = len(color_presets)
        requested_preset_count = int(self.configuration.get("number_of_presets"))
        for i in range(requested_preset_count):
            column_layout = QVBoxLayout()
            select_button = QPushButton("Sel", w)
            select_button.setEnabled(for_player)
            select_button.clicked.connect(lambda _=None, _i=i: self._select_color(_i))
            column_layout.addWidget(select_button)
            color_label = QWidget(w)
            color_label.setMinimumWidth(16)
            color_label.setMinimumHeight(16)
            color_label.setAutoFillBackground(True)
            if i < stored_preset_count:
                c = color_presets[i]
            else:
                # Grow the preset list with a default so the slot persists through save/reload.
                c = self._DEFAULT_PRESET.copy()
                color_presets.append(c)
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
        # Persist any defaults we materialized above so they survive serialization.
        self._serialize_presets()
        w.setLayout(layout)
        return w

    def get_player_widget(self, parent: QWidget | None) -> QWidget:
        """Return a fresh ``ColorPickerWidget`` wired to push picks to the show runtime."""
        if self._player_picker_widget:
            self._player_picker_widget.deleteLater()
        self._player_picker_widget = ColorPickerWidget(parent)
        self._player_picker_widget.color = self._value
        self._player_picker_widget.color_changed.connect(self.push_value)
        return self._player_picker_widget

    def get_configuration_widget(self, parent: QWidget | None) -> QWidget:
        """Return the preset-row widget shown inside the UI-editor configuration surface."""
        if not self._config_preset_row_widget:
            self._config_preset_row_widget = self._build_base_widget(parent, for_player=False)
        return self._config_preset_row_widget

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
        for preset in self._presets:
            preset_list.addItem(preset.format_for_filter())
        layout.addWidget(preset_list)
        w.setLayout(layout)
        self._dialog_preset_list = preset_list
        add_action.triggered.connect(lambda: self._open_add_preset_dialog(w))
        return w

    def _open_add_preset_dialog(self, parent: QWidget) -> None:
        """Show a modal ``QColorDialog`` that appends the chosen color to the preset list."""
        d = QColorDialog(parent)
        d.colorSelected.connect(self._add_preset)
        d.show()

    def _add_preset(self, c_template: QColor) -> None:
        """Append a new preset from the given Qt color and refresh the dependent UI."""
        c: ColorHSI = ColorHSI.from_qt_color(c_template)
        self._presets.append(c)
        self._serialize_presets()
        if self._dialog_preset_list is not None:
            self._dialog_preset_list.addItem(c.format_for_filter())
        self._rebuild_preset_views()

    def _select_color(self, i: int) -> None:
        if self._player_picker_widget is None:
            return
        d = QColorDialog(self._player_picker_widget)
        d.colorSelected.connect(lambda color: self._set_preset(i, color))
        d.show()

    def _set_preset(self, i: int, color: QColor) -> None:
        """Replace preset ``i`` with ``color``, persisting the change and refreshing UI."""
        if not (0 <= i < len(self._presets)):
            return
        self._presets[i] = ColorHSI.from_qt_color(color)
        self._serialize_presets()
        if self._dialog_preset_list is not None and i < self._dialog_preset_list.count():
            self._dialog_preset_list.item(i).setText(self._presets[i].format_for_filter())
        self._rebuild_preset_views()
