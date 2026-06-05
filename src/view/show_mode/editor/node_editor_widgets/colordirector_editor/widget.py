"""Contains node editor widget."""

from __future__ import annotations
from typing import TYPE_CHECKING, override

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QTabWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QMenu, \
    QTableWidget

from model.color_hsi import ColorHSI
from model.virtual_filters.colordirector_vfilter import ColordirectorVFilter, ColorPreset
from view.show_mode.editor.node_editor_widgets import NodeEditorFilterConfigWidget
from view.show_mode.editor.show_browser.annotated_item import AnnotatedTableWidgetItem

if TYPE_CHECKING:
    from model import Filter


class ColordirectorEditorWidget(NodeEditorFilterConfigWidget):
    """Configuration widget for Color Director.

    Provides a tab for the color groups, one for the presets and one for the recalls.

    """

    def __init__(self, model: Filter, parent: QWidget | None = None) -> None:
        super().__init__()
        if not isinstance(model, ColordirectorVFilter):
            raise TypeError("Color Director filter must be a ColordirectorVFilter.")
        self._model: ColordirectorVFilter = model
        self._widget = QTabWidget(parent)
        self._widget.setMinimumWidth(800)
        color_groups_tab = QWidget(self._widget)
        color_groups_layout = QVBoxLayout()
        color_groups_layout.addWidget(QLabel("Color Groups: TreeWidget"))
        color_groups_tab.setLayout(color_groups_layout)
        self._widget.addTab(color_groups_tab, "Color Groups")

        presets_tab = QWidget(self._widget)
        presets_layout = QVBoxLayout()
        preset_buttons_layout = QHBoxLayout()
        self._load_default_colors_button = QPushButton("Load default colors")

        add_default_color_menu = QMenu(self._widget)
        add_default_color_menu.addAction("Add short default color list", self._load_default_colors_clicked_short)
        add_default_color_menu.addAction("Add long default color list", self._load_default_colors_clicked_long)
        self._load_default_colors_button.setMenu(add_default_color_menu)
        preset_buttons_layout.addWidget(self._load_default_colors_button)

        self._add_preset_button = QPushButton("Add preset")
        self._add_preset_button.clicked.connect(self._add_preset)
        preset_buttons_layout.addWidget(self._add_preset_button)

        preset_buttons_layout.addStretch()
        presets_layout.addLayout(preset_buttons_layout)
        presets_layout.addWidget(QLabel("Presets: TableWidget with rows=preset columns=colors,fadetimes"))
        self._preset_table = QTableWidget(presets_tab)
        presets_layout.addWidget(self._preset_table)
        presets_tab.setLayout(presets_layout)
        self._widget.addTab(presets_tab, "Presets")

        recall_tab = QWidget(self._widget)
        recall_layout = QVBoxLayout()
        recall_layout.addWidget(QLabel("Recalls: TableWidget rows=recall columns=index"))
        recall_tab.setLayout(recall_layout)
        self._widget.addTab(recall_tab, "Recalls")

    @override
    def _get_configuration(self) -> dict[str, str]:
        return {}

    @override
    def _load_configuration(self, conf: dict[str, str]) -> None:
        pass

    @override
    def get_widget(self) -> QWidget:
        return self._widget

    @override
    def _load_parameters(self, parameters: dict[str, str]) -> dict:
        pass

    @override
    def _get_parameters(self) -> dict[str, str]:
        pass

    @override
    def parent_opened(self) -> None:
        super().parent_opened()
        pass  # TODO update outputs of filter

    def _reload_presets_table(self) -> None:
        tw = self._preset_table
        tw.clear()
        row_sum = 0
        for preset in self._model.presets:
            row_sum += len(preset.colors)
        tw.setRowCount(row_sum)
        tw.setColumnCount(self._model.get_ambient_color_count() + 4)
        offsets = 0
        for i, preset in enumerate(self._model.presets):
            index_widget = AnnotatedTableWidgetItem(str(i))
            index_widget.setFlags(index_widget.flags() ^ Qt.ItemFlag.ItemIsEditable)
            tw.setItem(i + offsets, 0, index_widget)
            first_iteration = True
            preset_index = -1
            for fade_in_time, transfer_function, ambient_colors in preset.colors:
                if not first_iteration:
                    offsets += 1
                first_iteration = False
                preset_index += 1

                fade_in_item = AnnotatedTableWidgetItem(f"{(fade_in_time * 40) / 1000:.3f}s")
                fade_in_item.annotated_data = (i, preset_index, 0)
                # TODO implement editing
                tw.setItem(i + offsets, 1, fade_in_item)

                transfer_item = AnnotatedTableWidgetItem(transfer_function.value)
                transfer_item.annotated_data = (i, preset_index, 1)
                # TODO implement editing
                tw.setItem(i + offsets, 2, transfer_item)

                add_accent_color_button = AnnotatedTableWidgetItem(" + ")
                add_accent_color_button.annotated_data = (i, preset_index, 2)
                tw.setItem(i + offsets, 3, add_accent_color_button)
                add_accent_color_button = QPushButton("+")
                add_accent_color_button.setToolTip("Add accent color to step.")
                add_accent_color_button.clicked.connect(lambda _, ac=ambient_colors: self._add_accent_color(ac))
                tw.setCellWidget(i + offsets, 3, add_accent_color_button)

                for color_index, accent_color in enumerate(ambient_colors):
                    accent_color_item = AnnotatedTableWidgetItem("   ")
                    accent_color_item.setToolTip(
                        f"H: {accent_color.hue} S: {accent_color.saturation} I: {accent_color.intensity
                        }\n{accent_color}"
                    )
                    accent_color_item.annotated_data = (i, preset_index, 3 + color_index)
                    accent_color_item.setBackground(accent_color.to_qt_color())
                    # TODO make editable
                    tw.setItem(i + offsets, 4 + color_index, accent_color_item)
            pass # TODO add option to add additional steps for last step

    def _load_default_colors_clicked_short(self) -> None:
        self._model.populate_presets_with_initial_data(True)
        self._reload_presets_table()

    def _load_default_colors_clicked_long(self) -> None:
        self._model.populate_presets_with_initial_data(False)
        self._reload_presets_table()

    def _add_preset(self) -> None:
        self._model.presets.append(ColorPreset())
        self._reload_presets_table()

    def _add_accent_color(self, ambient_color_list: list[ColorHSI]) -> None:
        ambient_color_list.append(ColorHSI(0.0, 0.0, 1.0))
        self._reload_presets_table()