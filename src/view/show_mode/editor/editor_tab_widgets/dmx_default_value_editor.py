"""Contains DMX default value editor tab widget."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from view.show_mode.editor.show_browser.annotated_item import AnnotatedListWidgetItem

if TYPE_CHECKING:
    from model.scene import Scene


class _ValueQueryDialog(QDialog):
    def __init__(self, parent: DMXDefaultValueEditorWidget) -> None:
        super().__init__(parent)
        self._editor: DMXDefaultValueEditorWidget = parent

        self._universe_id_tb = QComboBox()
        for univ in parent.scene.board_configuration.universes:
            self._universe_id_tb.addItem(str(univ.name), univ.id)
        self._channel_tb = QSpinBox()
        self._channel_tb.setRange(0, 511)
        self._value_tb = QSpinBox()
        self._value_tb.setRange(0, 255)

        layout = QFormLayout()
        layout.addRow("Universe ID", self._universe_id_tb)
        layout.addRow("Channel", self._channel_tb)
        layout.addRow("Value", self._value_tb)

        layout_exit = QHBoxLayout()
        self._ok = QPushButton()
        self._ok.setText("Enter")
        _cancel = QPushButton()
        _cancel.setText("Cancel")
        layout_exit.addWidget(_cancel)
        layout_exit.addWidget(self._ok)
        _cancel.setAutoDefault(False)
        self._ok.setAutoDefault(True)
        self._ok.clicked.connect(self._accept)
        _cancel.clicked.connect(self.close)
        layout.addRow(layout_exit)

        self.setLayout(layout)
        self.setWindowTitle("Add Entry")
        self.setModal(True)

    def _accept(self) -> None:
        univ_id = self._universe_id_tb.currentData()
        channel = self._channel_tb.value()
        value = self._value_tb.value()
        refresh_required = self._editor.scene.insert_dmx_default_value(univ_id, channel, value, supress_emission=True)
        if refresh_required:
            self._editor.refresh()
        else:
            self._editor.add_value_entry(univ_id, channel, value)
        self.close()


class DMXDefaultValueEditorWidget(QWidget):
    """Widget to edit default DMX value mappings."""

    def __init__(self, scene: Scene, parent: QWidget | None = None) -> None:
        """Initializes the widget.

        Args:
            scene: The scene which default DMX values should be edited.
            parent: The parent widget.

        """
        super().__init__(parent)
        self._scene: Scene = scene
        self._scene.default_values_changed.connect(self.refresh)

        layout = QVBoxLayout()

        self._value_list_widget = QListWidget()
        self._value_list_widget.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding))
        self._value_list_widget.setSelectionMode(QListWidget.SelectionMode.MultiSelection)

        self._remove_value_button = QPushButton("Remove Default Value")
        self._remove_value_button.clicked.connect(self._remove_entry)

        self.refresh()

        self._add_value_button = QPushButton("Add Default Value")
        self._add_value_button.clicked.connect(self._add_value_clicked)

        layout.addWidget(QLabel(f"DMX Default Values of Scene '{scene.human_readable_name}' [{scene.scene_id}]"))
        layout.addWidget(self._value_list_widget)
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        buttons_layout.addWidget(self._remove_value_button)
        buttons_layout.addSpacing(25)
        buttons_layout.addWidget(self._add_value_button)
        layout.addLayout(buttons_layout)

        self.setLayout(layout)

    def refresh(self) -> None:
        """Refreshes the list view."""
        self._value_list_widget.clear()
        empty = True
        for univ_id, channel, value in self._scene.dmx_default_values:
            self.add_value_entry(univ_id, channel, value)
            empty = False
        self._remove_value_button.setEnabled(not empty)

    @property
    def scene(self) -> Scene:
        """Get the scene in use."""
        return self._scene

    def _add_value_clicked(self) -> None:
        self._dialog = _ValueQueryDialog(self)
        self._dialog.show()

    def add_value_entry(self, universe_id: int, channel: int, value: int) -> None:
        """Add an entry to the list view."""
        item = AnnotatedListWidgetItem(self._value_list_widget)
        item.annotated_data = (universe_id, channel, value)
        capability = ""
        associated_fixture = self._scene.board_configuration.get_fixture_by_address(universe_id, channel)
        if associated_fixture is not None:
            capability = associated_fixture.fixture_channels[channel - associated_fixture.start_index].name
        item.setText(f"{universe_id}:{channel} ({associated_fixture.name if
            associated_fixture is not None else ""}.{capability}) -> {value}")
        self._remove_value_button.setEnabled(True)

    def _remove_entry(self) -> None:
        for entry_item in self._value_list_widget.selectedItems():
            if not isinstance(entry_item, AnnotatedListWidgetItem):
                continue
            univ, channel, _ = entry_item.annotated_data
            self.scene.remove_dmx_default_value(univ, channel, supress_emission=True)
        self.refresh()
