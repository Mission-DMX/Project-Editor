# coding=utf-8
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (QCheckBox, QHBoxLayout, QTableWidget, QTableWidgetItem, QToolBar, QTreeWidget,
                               QTreeWidgetItem, QVBoxLayout, QWidget)

from model import Filter
from model.scene import FilterPage
from view.show_mode.editor.node_editor_widgets import NodeEditorFilterConfigWidget
from view.show_mode.editor.show_browser.annotated_item import AnnotatedTreeWidgetItem
from view.utility_widgets.filter_selection_widget import FilterSelectionWidget


class ImportVFilterSettingsWidget(NodeEditorFilterConfigWidget):

    def __init__(self, imp_filter: Filter, parent: QWidget = None):
        super().__init__()
        self._widget: QWidget | None = None
        self._tree_widget: FilterSelectionWidget | None = None
        self.__rename_table_widget: QTableWidget | None = None
        self._rename_dict: dict[str, str] = {}
        self._enabled_cb_dict: dict[str, QCheckBox] = {}
        self._new_name_item_dict: dict[str, QTableWidgetItem] = {}
        self._filter = imp_filter
        self._parent = parent
        self._last_selected_item: QTreeWidgetItem | None = None

    def _get_configuration(self) -> dict[str, str]:
        renaming_data = []
        for orig_channel_name in self._new_name_item_dict.keys():
            renaming_data.append(f"{orig_channel_name}={self._new_name_item_dict.get(orig_channel_name).text()
            if self._enabled_cb_dict[orig_channel_name].checkState() == Qt.CheckState.Checked
            else ""}"
                                 )
        selected_filter = self._tree_widget.selected_filter
        return {
            "target": selected_filter.filter_id if selected_filter is not None else "",
            "rename_dict": ",".join(renaming_data)
        }

    def _load_configuration(self, conf: dict[str, str]):
        target_filter_id = conf.get("target") or ""
        if self._widget is None:
            self._construct_widget()
        self._tree_widget.selected_filter = self._filter.scene.get_filter_by_id(target_filter_id)
        self._rename_dict.clear()
        for entry in (conf.get("rename_dict") or "").split(","):
            if "=" not in entry:
                continue
            k, v = entry.split("=")
            self._rename_dict[k] = v
        self._populate_widget()

    def get_widget(self) -> QWidget:
        if self._widget is None:
            self._construct_widget()
        return self._widget

    def _load_parameters(self, parameters: dict[str, str]):
        pass

    def _get_parameters(self) -> dict[str, str]:
        return dict()

    def _construct_widget(self):
        self._widget = QWidget(parent=self._parent)
        layout = QVBoxLayout()
        toolbar = QToolBar()
        self._clear_selection_action = QAction('Clear Selection')
        self._clear_selection_action.setEnabled(False)
        toolbar.addAction(self._clear_selection_action)
        toolbar.addSeparator()
        self._select_all_action = QAction('Select All')
        self._select_all_action.triggered.connect(self._select_all_channels)
        toolbar.addAction(self._select_all_action)
        self._deselect_all_action = QAction('Deselect All')
        self._deselect_all_action.triggered.connect(self._deselect_all_channels)
        toolbar.addAction(self._deselect_all_action)
        layout.addWidget(toolbar)
        selection_layout = QHBoxLayout()
        layout.addLayout(selection_layout)
        self._tree_widget = FilterSelectionWidget(self._widget, self._filter.scene, None)
        self._tree_widget.selectionModel().selectionChanged.connect(self._selection_changed)
        selection_layout.addWidget(self._tree_widget)
        self._rename_table_widget = QTableWidget(parent=self._widget)
        self._rename_table_widget.setColumnCount(3)
        selection_layout.addWidget(self._rename_table_widget)
        self._widget.setLayout(layout)
        self._populate_widget()

    def _load_rename_table(self):
        self._rename_table_widget.clear()
        self._enabled_cb_dict.clear()
        self._new_name_item_dict.clear()
        target = self._tree_widget.selected_filter
        if target is None:
            self._rename_table_widget.setRowCount(0)
            return
        output_channel_list = target.out_data_types.keys()
        self._rename_table_widget.setRowCount(len(output_channel_list))
        i = 0
        for channel_name in output_channel_list:
            new_name = self._rename_dict.get(channel_name)
            enabled_item = QTableWidgetItem()
            enabled_item.setFlags(enabled_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            self._rename_table_widget.setItem(i, 0, enabled_item)
            cb = QCheckBox()
            cb.setCheckState(Qt.CheckState.Checked if new_name != "" else Qt.CheckState.Unchecked)
            self._enabled_cb_dict[channel_name] = cb
            self._rename_table_widget.setCellWidget(i, 0, cb)
            orig_name_item = QTableWidgetItem(channel_name)
            orig_name_item.setFlags(
                orig_name_item.flags() & ~Qt.ItemFlag.ItemIsEditable & ~Qt.ItemFlag.ItemIsSelectable)
            self._rename_table_widget.setItem(i, 1, orig_name_item)
            new_name_item = QTableWidgetItem(new_name if new_name is not None and new_name != "" else channel_name)
            new_name_item.setFlags(new_name_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            self._new_name_item_dict[channel_name] = new_name_item
            self._rename_table_widget.setItem(i, 2, new_name_item)
            i += 1

    def _selection_changed(self):
        self._load_rename_table()
        self._clear_selection_action.setEnabled(True)
        # TODO issue a warning here if self._target_filter_id changed

    def _select_all_channels(self):
        for i in range(self._rename_table_widget.rowCount()):
            c_item = self._rename_table_widget.cellWidget(i, 0)
            if not isinstance(c_item, QCheckBox):
                continue
            c_item.setCheckState(Qt.CheckState.Checked)

    def _deselect_all_channels(self):
        for i in range(self._rename_table_widget.rowCount()):
            c_item = self._rename_table_widget.cellWidget(i, 0)
            if not isinstance(c_item, QCheckBox):
                continue
            c_item.setCheckState(Qt.CheckState.Unchecked)

    def _populate_widget(self):
        if self._widget is None:
            self._construct_widget()
            return
        self._tree_widget.populate_widget()
        self._load_rename_table()

    def parent_opened(self):
        self._populate_widget()
