"""Contains QWidget instantiated by UI Widget adapter."""
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QGridLayout, QLabel, QPushButton, QWidget

from view.show_mode.show_ui_widgets.colordirector._preview_bitmap_generator import PreviewBitmapGenerator
from view.utility_widgets.jogwheel_spinbox import JogwheelSpinBox

if TYPE_CHECKING:
    from PySide6.QtGui import QPixmap

    from model.virtual_filters.colordirector_vfilter import ColordirectorVFilter

class ControllerWidget(QWidget):
    """Widget provides button matrix, group labels and recall field."""

    def __init__(self, model: ColordirectorVFilter,
                 update_list: list[tuple[str, str]] | None,
                 parent: QWidget | None = None) -> None:
        """Initialize and generate button matrix."""
        super().__init__(parent)
        self._update_list: list[tuple[str, str]] | None = update_list
        element_size = 64
        self._model = model
        number_of_groups = len(model.output_groups.keys())
        number_of_presets = len(model.presets)
        layout = QGridLayout()
        self._recall_sp = JogwheelSpinBox()
        self._recall_sp.value_submitted.connect(self._recall_issued)
        recall_count = len(model.recalls)
        self._recall_sp.setRange(0, recall_count)
        self._recall_sp.setEnabled(recall_count > 0)
        # TODO connect recall enter event and enable jog wheel
        self._recall_sp.setMaximumSize(100, element_size)
        layout.addWidget(self._recall_sp, 0, 0)
        output_group_list = list(model.output_groups.keys())
        for i, group in enumerate(output_group_list):
            label = QLabel(group)
            label.setWordWrap(True)
            label.setFixedWidth(100)
            label.setMaximumHeight(element_size)
            layout.addWidget(label, i + 1, 0)
        self._apply_group_buttons = []
        for i in range(number_of_presets):
            group_button = QPushButton("🠋")
            group_button.setFixedSize(element_size, element_size)
            group_button.clicked.connect(lambda _,ii=i: self._apply_whole_group_clicked(ii))
            self._apply_group_buttons.append(group_button)
            layout.addWidget(group_button, 0, i + 1)
        self._apply_single_buttons: list[list[QPushButton]] = []
        self._preview_generator = PreviewBitmapGenerator(model.presets, size=element_size)
        for y in range(len(model.presets)):
            preset_buttons = []
            for x in range(len(output_group_list)):
                button = QPushButton()
                button.setFixedSize(element_size, element_size)
                button.clicked.connect(lambda _,preset_i=y,group_i=x: self._apply_single_clicked(group_i, preset_i))
                preset_buttons.append(button)
                layout.addWidget(button, x + 1, y + 1)
            self._apply_single_buttons.append(preset_buttons)
        self._preview_generator.preset_preview_generated.connect(self._add_preview_on_buttons)
        self._preview_generator.finished.connect(self._delete_preview_generator)
        self.setMinimumSize(number_of_presets * element_size + 100, (number_of_groups + 1) * element_size)
        self.setLayout(layout)
        self._preview_generator.start()
        # TODO implement buttons with active color being down

    def _apply_whole_group_clicked(self, preset_index: int) -> None:
        pass  # TODO

    def _apply_single_clicked(self, group_index: int, preset_index: int) -> None:
        pass  # TODO

    def _recall_issued(self, recall_index: int) -> None:
        pass  # TODO

    def _add_preview_on_buttons(self, preview_index: int, image: QPixmap) -> None:
        icon_size = self._apply_single_buttons[0][0].size()
        icon_size.setWidth(int(icon_size.width() * 0.75))
        icon_size.setHeight(int(icon_size.height() * 0.75))
        for button in self._apply_single_buttons[preview_index]:
            button.setIcon(image)
            button.setIconSize(icon_size)

    def _delete_preview_generator(self) -> None:
        if self._preview_generator is not None:
            self._preview_generator.deleteLater()
        self._preview_generator = None
