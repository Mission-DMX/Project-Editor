"""Contains settings dialog class."""

from typing import TYPE_CHECKING

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QSpinBox,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from view.show_mode.player.external_ui_windows import update_window_count

if TYPE_CHECKING:
    from model import BoardConfiguration


class SettingsDialog(QDialog):
    """Settings dialog class.

    Class provides settings that are stored in show file.
    """

    def __init__(self, parent: QWidget | None, show: "BoardConfiguration") -> None:
        """Initialize the dialog."""
        super().__init__(parent)
        self.setMinimumHeight(300)
        self.setMinimumWidth(300)
        self.setWindowTitle("Setting: " + show.show_name)
        exit_buttons = (QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Apply |
                        QDialogButtonBox.StandardButton.Cancel)

        self._category_tab_bar = QTabWidget(self)
        self._general_settings_tab = QWidget(self._category_tab_bar)
        general_layout = QFormLayout()
        self.show_file_tb = QLineEdit(self._general_settings_tab)
        general_layout.addRow("Show File Name: ", self.show_file_tb)
        self.show_notes_tb = QTextEdit(self._general_settings_tab)
        general_layout.addRow("Notes: ", self.show_notes_tb)
        self._general_settings_tab.setLayout(general_layout)
        self._category_tab_bar.addTab(self._general_settings_tab, "General")

        self._play_tab = QWidget(self._category_tab_bar)
        play_layout = QFormLayout()
        self._default_main_brightness_tb = QSpinBox(self._play_tab)
        self._default_main_brightness_tb.setMinimum(0)
        self._default_main_brightness_tb.setMaximum(255)
        self._default_main_brightness_tb.setToolTip("At which brightness level should the main fader be after the "
                                                    "show file has been loaded?")
        play_layout.addRow("Default Main Brightness", self._default_main_brightness_tb)
        self._play_tab.setLayout(play_layout)
        self._category_tab_bar.addTab(self._play_tab, "Play")

        self._editor_tab = QWidget(self._category_tab_bar)
        editor_layout = QFormLayout()
        self._brightness_mixin_enbled_cb = QCheckBox("Enable if no global dimmer", self._editor_tab)
        self._brightness_mixin_enbled_cb.setToolTip("If this is checked, a fixture that is added will automatically "
                                                    "connected to color brightness mixins, if no global dimmer is "
                                                    "present.")
        self._brightness_mixin_enbled_cb.setChecked(True)
        editor_layout.addRow("Brightness Mixins", self._brightness_mixin_enbled_cb)
        self._show_ui_window_count_tb = QSpinBox(self._editor_tab)
        self._show_ui_window_count_tb.setMinimum(0)
        self._show_ui_window_count_tb.setMaximum(1024)
        editor_layout.addRow("Additional UI Window Count", self._show_ui_window_count_tb)
        self._editor_tab.setLayout(editor_layout)
        self._category_tab_bar.addTab(self._editor_tab, "Editor")

        self.button_box = QDialogButtonBox(exit_buttons)
        self.button_box.accepted.connect(self._ok_button_pressed)
        self.button_box.rejected.connect(self._cancle_button_pressed)
        self.button_box.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self.apply)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self._category_tab_bar)
        self.layout.addWidget(self.button_box)
        self.setLayout(self.layout)
        self.show_file = show
        self.setModal(True)
        self.setVisible(True)

    @property
    def show_file(self) -> "BoardConfiguration":
        """Get or set show file whose settings should be edited."""
        return self._show

    @show_file.setter
    def show_file(self, new_show: "BoardConfiguration") -> None:
        self._show = new_show
        self.show_file_tb.setText(new_show.show_name)
        self.show_notes_tb.setText(new_show.notes)
        self._brightness_mixin_enbled_cb.setChecked(
            str(new_show.ui_hints.get("color-mixin-auto-add-disabled")).lower() != "true")
        try:
            self._default_main_brightness_tb.setValue(int(new_show.ui_hints.get("default_main_brightness") or "255"))
        except ValueError:
            self._default_main_brightness_tb.setValue(255)
        try:
            self._show_ui_window_count_tb.setValue(int(new_show.ui_hints.get("show_ui_window_count", "0")))
        except ValueError:
            self._show_ui_window_count_tb.setValue(0)

    def apply(self) -> None:
        """Apply the current dialed in settings."""
        self._show.show_name = self.show_file_tb.text()
        self._show.notes = self.show_notes_tb.toPlainText()
        self._show.ui_hints["default_main_brightness"] = str(self._default_main_brightness_tb.value())
        self._show.ui_hints[
            "color-mixin-auto-add-disabled"] = "false" if self._brightness_mixin_enbled_cb.isChecked() else "true"
        self._show.ui_hints["show_ui_window_count"] = str(self._show_ui_window_count_tb.value())
        update_window_count(self._show_ui_window_count_tb.value(), self._show)

    def _ok_button_pressed(self) -> None:
        self.apply()
        self.accept()

    def _cancle_button_pressed(self) -> None:
        self.reject()
