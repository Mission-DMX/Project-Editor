from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QTreeWidget, QTreeWidgetItem

from model import Filter
from model.scene import FilterPage
from view.show_mode.editor.node_editor_widgets import NodeEditorFilterConfigWidget
from view.show_mode.editor.show_browser.annotated_item import AnnotatedTreeWidgetItem


class ImportVFilterSettingsWidget(NodeEditorFilterConfigWidget):

    def __init__(self, imp_filter: Filter, parent: QWidget = None):
        super().__init__()
        self._widget: QTreeWidget | None = None
        self._target_filter_id: str = ""
        self._filter = imp_filter
        self._parent = parent
        self._last_selected_item: QTreeWidgetItem | None = None

    def _get_configuration(self) -> dict[str, str]:
        return {"target": self._target_filter_id}

    def _load_configuration(self, conf: dict[str, str]):
        self._target_filter_id = conf.get("target") or ""
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
        self._widget = QTreeWidget(parent=self._parent)
        self._widget.selectionModel().selectionChanged.connect(self._selection_changed)
        self._populate_widget()

    def _populate_widget(self):
        if self._widget is None:
            self._construct_widget()
            return
        already_added_filters = set()
        fp_index = 0
        target_scene = self._filter.scene
        self._widget.clear()
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
            page_item = AnnotatedTreeWidgetItem(self._widget if parent is None else parent)
            page_item.setText(0, filter_page.name)
            page_item.setExpanded(True)
            page_item.setFlags(page_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            for filter_to_add in fp.filters:
                add_filter_item(filter_to_add, page_item)
            for sub_page in fp.child_pages:
                add_filter_page(sub_page, page_item)
            if parent is None:
                self._widget.insertTopLevelItem(fp_index, page_item)
                fp_index += 1

        for filter_page in target_scene.pages:
            add_filter_page(filter_page, None)

        for t_filter in target_scene.filters:
            if t_filter not in already_added_filters:
                self._widget.insertTopLevelItem(fp_index, add_filter_item(t_filter, self._widget))
                fp_index += 1

    def _find_selected_filter(self):
        for selected_filter_item in self._widget.selectedItems():
            if isinstance(selected_filter_item, AnnotatedTreeWidgetItem):
                ad = selected_filter_item.annotated_data
                if isinstance(ad, Filter):
                    self._target_filter_id = ad.filter_id
                    return
        self._target_filter_id = ""

    def _selection_changed(self):
        sitems = self._widget.selectedItems()
        if len(sitems) == 0 and self._last_selected_item is not None:
            self._last_selected_item.setSelected(True)
        self._find_selected_filter()

    def parent_opened(self):
        self._populate_widget()
