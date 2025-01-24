from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QTreeWidget, QTreeWidgetItem, QHBoxLayout, QTableWidget, QTableWidgetItem, \
    QCheckBox

from model import Filter
from model.scene import FilterPage
from view.show_mode.editor.node_editor_widgets import NodeEditorFilterConfigWidget
from view.show_mode.editor.show_browser.annotated_item import AnnotatedTreeWidgetItem


class ImportVFilterSettingsWidget(NodeEditorFilterConfigWidget):

    def __init__(self, imp_filter: Filter, parent: QWidget = None):
        super().__init__()
        self._widget: QWidget | None = None
        self._tree_widget: QTreeWidget | None = None
        self.__rename_table_widget: QTableWidget | None = None
        self._target_filter_id: str = ""
        self._rename_dict: dict[str, str] = {}
        self._enabled_cb_dict: dict[str, QCheckBox] = {}
        self._new_name_item_dict: dict[str, QTableWidgetItem] = {}
        self._filter = imp_filter
        self._parent = parent
        self._last_selected_item: QTreeWidgetItem | None = None

    def _get_configuration(self) -> dict[str, str]:
        renaming_data = []
        for orig_channel_name in self._new_name_item_dict.keys():
            renaming_data.append("{}={}".format(
                orig_channel_name,
                self._new_name_item_dict.get(orig_channel_name).text()
                if self._enabled_cb_dict[orig_channel_name].checkState() == Qt.CheckState.Checked
                else "")
            )
        return {
            "target": self._target_filter_id,
            "rename_dict": ",".join(renaming_data)
        }

    def _load_configuration(self, conf: dict[str, str]):
        self._target_filter_id = conf.get("target") or ""
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
        layout = QHBoxLayout()
        self._widget.setLayout(layout)
        self._tree_widget = QTreeWidget(parent=self._widget)
        self._tree_widget.selectionModel().selectionChanged.connect(self._selection_changed)
        layout.addWidget(self._tree_widget)
        self._rename_table_widget = QTableWidget(parent=self._widget)
        self._rename_table_widget.setColumnCount(3)
        layout.addWidget(self._rename_table_widget)
        self._populate_widget()

    def _populate_widget(self):
        if self._widget is None:
            self._construct_widget()
            return
        already_added_filters = set()
        fp_index = 0
        target_scene = self._filter.scene
        self._tree_widget.clear()
        self._last_selected_item = None

        def add_filter_item(filter_to_add: Filter, page_item):
            nonlocal already_added_filters
            filter_item = AnnotatedTreeWidgetItem(page_item)
            filter_item.setText(0, filter_to_add.filter_id)
            filter_item.annotated_data = filter_to_add
            if filter_to_add.filter_id == self._target_filter_id:
                filter_item.setSelected(True)
                self._last_selected_item = filter_item
            if filter_to_add == self._filter:
                filter_item.setHidden(True)
                filter_item.setFlags(filter_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            already_added_filters.add(filter_to_add)
            return filter_item

        def add_filter_page(fp: FilterPage, parent: AnnotatedTreeWidgetItem | None):
            nonlocal fp_index
            page_item = AnnotatedTreeWidgetItem(self._tree_widget if parent is None else parent)
            page_item.setText(0, filter_page.name)
            page_item.setExpanded(True)
            page_item.setFlags(page_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            for filter_to_add in fp.filters:
                add_filter_item(filter_to_add, page_item)
            for sub_page in fp.child_pages:
                add_filter_page(sub_page, page_item)
            if parent is None:
                self._tree_widget.insertTopLevelItem(fp_index, page_item)
                fp_index += 1

        for filter_page in target_scene.pages:
            add_filter_page(filter_page, None)

        for t_filter in target_scene.filters:
            if t_filter not in already_added_filters:
                self._tree_widget.insertTopLevelItem(fp_index, add_filter_item(t_filter, self._widget))
                fp_index += 1
        self._load_rename_table()

    def _load_rename_table(self):
        self._rename_table_widget.clear()
        self._enabled_cb_dict.clear()
        self._new_name_item_dict.clear()
        target = self._filter.scene.get_filter_by_id(self._target_filter_id)
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
            orig_name_item.setFlags(orig_name_item.flags() & ~Qt.ItemFlag.ItemIsEditable & ~Qt.ItemFlag.ItemIsSelectable)
            self._rename_table_widget.setItem(i, 1, orig_name_item)
            new_name_item = QTableWidgetItem(new_name if new_name is not None and new_name != "" else channel_name)
            new_name_item.setFlags(new_name_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            self._new_name_item_dict[channel_name] = new_name_item
            self._rename_table_widget.setItem(i, 2, new_name_item)
            i += 1

    def _find_selected_filter(self):
        for selected_filter_item in self._tree_widget.selectedItems():
            if isinstance(selected_filter_item, AnnotatedTreeWidgetItem):
                ad = selected_filter_item.annotated_data
                if isinstance(ad, Filter):
                    self._target_filter_id = ad.filter_id
                    return
        # we do not clear out the last selected item in case of non-filter selection

    def _selection_changed(self):
        sitems = self._tree_widget.selectedItems()
        if len(sitems) == 0 and self._last_selected_item is not None:
            self._last_selected_item.setSelected(True)
        self._find_selected_filter()
        self._load_rename_table()
        # TODO issue a warning here if self._target_filter_id changed

    def parent_opened(self):
        self._populate_widget()
