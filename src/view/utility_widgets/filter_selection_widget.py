# coding=utf-8
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTreeWidget, QWidget

from model import Scene
from model.filter import Filter, FilterTypeEnumeration
from model.scene import FilterPage
from view.show_mode.editor.show_browser.annotated_item import AnnotatedTreeWidgetItem


class FilterSelectionWidget(QTreeWidget):
    def __init__(self, parent: QWidget | None, scene: Scene, allowed_filter_types: list[FilterTypeEnumeration] | None):
        super().__init__(parent)
        self._scene = scene
        self._target_filter_id: str | None = None
        self._filter: Filter | None = None
        self._id_to_item_dict: dict[str, AnnotatedTreeWidgetItem] = {}
        self._last_selected_item: AnnotatedTreeWidgetItem | None = None
        self.selectionModel().selectionChanged.connect(self._selection_changed)
        self._allowed_filter_types = allowed_filter_types or []

        self.populate_widget()

    @property
    def selected_filter(self) -> Filter | None:
        return self._filter

    @selected_filter.setter
    def selected_filter(self, f: Filter | None):
        self.clearSelection()
        if f is not None:
            self._target_filter_id = f.filter_id
            self._filter = None
            filter_item = self._id_to_item_dict.get(f.filter_id)
            if filter_item is not None:
                filter_item.setSelected(True)
                self._last_selected_item = filter_item
        else:
            self._target_filter_id = None
            self._filter = None

    def populate_widget(self):
        already_added_filters = set()
        fp_index = 0
        target_scene = self._scene
        self.clear()
        self._id_to_item_dict.clear()
        self._last_selected_item = None

        def is_filter_addable(filter_to_add: Filter) -> bool:
            if len(self._allowed_filter_types) > 0:
                if filter_to_add.filter_type not in self._allowed_filter_types:
                    return False
            return True

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
            self._id_to_item_dict[filter_to_add.filter_id] = filter_item
            return filter_item

        def add_filter_page(fp: FilterPage, parent: AnnotatedTreeWidgetItem | None):
            nonlocal fp_index
            page_item = AnnotatedTreeWidgetItem(self if parent is None else parent)
            page_item.setText(0, filter_page.name)
            page_item.setExpanded(True)
            page_item.setFlags(page_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            for filter_to_add in fp.filters:
                if is_filter_addable(filter_to_add):
                    add_filter_item(filter_to_add, page_item)
            for sub_page in fp.child_pages:
                add_filter_page(sub_page, page_item)
            if parent is None:
                self.insertTopLevelItem(fp_index, page_item)
                fp_index += 1

        for filter_page in target_scene.pages:
            add_filter_page(filter_page, None)

        for t_filter in target_scene.filters:
            if t_filter not in already_added_filters:
                if is_filter_addable(t_filter):
                    self.insertTopLevelItem(fp_index, add_filter_item(t_filter, self.parent()))
                    fp_index += 1

    def _find_selected_filter(self):
        for selected_filter_item in self.selectedItems():
            if isinstance(selected_filter_item, AnnotatedTreeWidgetItem):
                ad = selected_filter_item.annotated_data
                if isinstance(ad, Filter):
                    self._target_filter_id = ad.filter_id
                    self._filter = ad
                    return
        # we do not clear out the last selected item in case of non-filter selection

    def _selection_changed(self):
        sitems = self.selectedItems()
        if len(sitems) == 0 and self._last_selected_item is not None:
            self._last_selected_item.setSelected(True)
        self._find_selected_filter()