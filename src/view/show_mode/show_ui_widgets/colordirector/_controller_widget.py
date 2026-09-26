"""Contains QWidget instantiated by UI Widget adapter."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Signal
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QGridLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget

from view.show_mode.show_ui_widgets.colordirector._preview_bitmap_generator import PreviewBitmapGenerator
from view.utility_widgets.jogwheel_spinbox import JogwheelSpinBox

if TYPE_CHECKING:
    from PySide6.QtGui import QImage

    from model.virtual_filters.colordirector_vfilter import ColordirectorVFilter


_ELEMENT_SIZE = 64
"""Edge length of the square preset and apply buttons in pixels."""

_GROUP_LABEL_WIDTH = 100
"""Width of the color group label column in pixels."""

_PREVIEW_ICON_SCALE = 0.75
"""Scale factor applied to preview bitmaps when using them as button icons."""

_APPLY_COLUMN_BUTTON_TEXT = "🠋"
"""Text of the buttons applying a preset to every color group at once."""


class ControllerWidget(QWidget):
    """Widget provides button matrix, group labels and recall field."""

    update_requested = Signal()

    def __init__(
        self,
        model: ColordirectorVFilter,
        update_list: list[tuple[str, str]] | None,
        feedback_enabled: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        """Initialize and generate the button matrix.

        Args:
            model: The color director filter providing the color groups, presets and recalls.
            update_list: The list the update messages to fish are collected within. If None, the widget does not
                collect any update messages since it is used to configure the show only.
            feedback_enabled: Whether the buttons of the currently active colors are highlighted using feedback
                messages sent by fish.
            parent: The parent widget.

        """
        super().__init__(parent)
        self._update_list: list[tuple[str, str]] | None = update_list
        self._model = model
        number_of_groups = len(model.output_groups)
        number_of_presets = len(model.presets)
        layout = QGridLayout()
        self._recall_sp = JogwheelSpinBox()
        if update_list is not None:
            self._recall_sp.value_submitted.connect(self._recall_issued)
        self._update_recall_spinbox()
        self._recall_sp.setMaximumSize(_GROUP_LABEL_WIDTH, _ELEMENT_SIZE)
        layout.addWidget(self._recall_sp, 0, 0)
        self._output_group_list = list(model.output_groups)
        for i, group in enumerate(self._output_group_list):
            label = QLabel(group)
            label.setWordWrap(True)
            label.setFixedWidth(_GROUP_LABEL_WIDTH)
            label.setMaximumHeight(_ELEMENT_SIZE)
            layout.addWidget(label, i + 1, 0)
        for i in range(number_of_presets):
            group_button = QPushButton(_APPLY_COLUMN_BUTTON_TEXT)
            group_button.setToolTip("Apply this preset to all color groups.")
            group_button.setFixedSize(_ELEMENT_SIZE, _ELEMENT_SIZE)
            if update_list is not None:
                group_button.clicked.connect(lambda _, ii=i: self._apply_column_clicked(ii))
            layout.addWidget(group_button, 0, i + 1)
        self._apply_single_buttons: list[list[QPushButton]] = []
        preview_generator = PreviewBitmapGenerator(model.presets, size=_ELEMENT_SIZE)
        for y in range(len(model.presets)):
            preset_buttons = []
            for x in range(len(self._output_group_list)):
                button = QPushButton()
                button.setFixedSize(_ELEMENT_SIZE, _ELEMENT_SIZE)
                if update_list is not None:
                    button.clicked.connect(
                        lambda _, preset_i=y, group_i=x: self._apply_single_clicked(group_i, preset_i)
                    )
                preset_buttons.append(button)
                layout.addWidget(button, x + 1, y + 1)
            self._apply_single_buttons.append(preset_buttons)
        preview_generator.preset_preview_generated.connect(self._add_preview_on_buttons)
        self.destroyed.connect(preview_generator.requestInterruption)
        grid_content = QWidget()
        grid_content.setLayout(layout)
        grid_content.setMinimumSize(
            number_of_presets * _ELEMENT_SIZE + _GROUP_LABEL_WIDTH, (number_of_groups + 1) * _ELEMENT_SIZE
        )
        scroll_area = QScrollArea()
        scroll_area.setWidget(grid_content)
        scroll_area.setWidgetResizable(True)
        outer_layout = QVBoxLayout()
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addWidget(scroll_area)
        self.setLayout(outer_layout)
        preview_generator.start()
        self._model.configuration_changed.mapped_signal.connect(self._update_recall_spinbox)
        if feedback_enabled:
            self._model.configuration_changed.mapped_signal.connect(self._active_colors_changed)

    def _apply_column_clicked(self, preset_index: int) -> None:
        """Enqueue the update messages applying the preset to every color group and request their transmission."""
        if self._update_list is None:
            return
        self._update_list.clear()
        self._update_list.extend(
            self._model.get_update_msg_for_group_preset_change(group_name, preset_index)
            for group_name in self._output_group_list
        )
        self.update_requested.emit()

    def _apply_single_clicked(self, group_index: int, preset_index: int) -> None:
        """Enqueue the update message applying the preset to the color group and request its transmission."""
        if self._update_list is None:
            return
        self._update_list.append(
            self._model.get_update_msg_for_group_preset_change(self._output_group_list[group_index], preset_index)
        )
        self.update_requested.emit()

    def _recall_issued(self, recall_index: int) -> None:
        """Enqueue the update messages applying the saved selection of the recall and request their transmission."""
        if self._update_list is None:
            return
        selection = self._model.get_recall_preset_selection(recall_index)
        if selection is None:
            return
        self._update_list.clear()
        self._update_list.extend(
            self._model.get_update_msg_for_group_preset_change(group_name, preset_index)
            for group_name, preset_index in selection
        )
        self.update_requested.emit()

    def _update_recall_spinbox(self) -> None:
        """Update the recall spin box to the recalls currently available in the model."""
        recall_count = len(self._model.recalls)
        self._recall_sp.setEnabled(recall_count > 0)
        self._recall_sp.setRange(0, max(recall_count - 1, 0))

    def _add_preview_on_buttons(self, preview_index: int, image: QImage) -> None:
        """Set the generated preview image as icon of all buttons applying the preset it was generated for.

        Args:
            preview_index: The index of the preset the image was generated for.
            image: The generated preview image.

        """
        if not 0 <= preview_index < len(self._apply_single_buttons):
            return
        buttons = self._apply_single_buttons[preview_index]
        if not buttons:
            return
        icon_size = buttons[0].size()
        icon_size.setWidth(int(icon_size.width() * _PREVIEW_ICON_SCALE))
        icon_size.setHeight(int(icon_size.height() * _PREVIEW_ICON_SCALE))
        icon = QIcon(QPixmap.fromImage(image))
        for button in buttons:
            button.setIcon(icon)
            button.setIconSize(icon_size)

    def _active_colors_changed(self) -> None:
        """Highlight the buttons of the colors currently active within their color group."""
        active_colors = self._model.get_current_active_colors()
        for i, group_buttons in enumerate(self._apply_single_buttons):
            for j, button in enumerate(group_buttons):
                active_color_in_group = active_colors[j] if j < len(active_colors) else -1
                button.setDown(i == active_color_in_group)
