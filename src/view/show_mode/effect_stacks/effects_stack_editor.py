from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QEnterEvent
from PySide6.QtWidgets import QWidget, QHBoxLayout, QTreeWidgetItem, QVBoxLayout, QSpinBox, QMessageBox, QScrollArea, \
    QSplitter

from controller.ofl.fixture import UsedFixture
from model import Filter
from model.virtual_filters.effects_stacks.vfilter import EffectsStack
from model.virtual_filters.effects_stacks.effect import Effect
from view.show_mode.editor.show_browser.annotated_item import AnnotatedTreeWidgetItem
from view.show_mode.editor.show_browser.universe_tree_browser_widget import UniverseTreeBrowserWidget
from view.show_mode.effect_stacks.effects_compilation_widget import EffectCompilationWidget
from view.show_mode.effect_stacks.effects_list import EffectsListWidget


class EffectsStackEditor(QWidget):

    def __init__(self, f: Filter, parent: QWidget | None):
        super().__init__(parent=parent)
        if not isinstance(f, EffectsStack):
            raise ValueError("This filter is supposed to be an instance of the EffectsStack virtual filter.")
        self._filter = f
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        global_layout = QHBoxLayout()
        self.setLayout(global_layout)
        self._effects_list_widget = EffectsListWidget(self)
        global_layout.addWidget(self._effects_list_widget)
        center_container = QWidget(self)
        center_layout = QVBoxLayout()
        center_container.setLayout(center_layout)
        self._compilation_widget = EffectCompilationWidget(f, center_container)
        self._compilation_widget.effect_added.connect(self._effect_added)
        self._compilation_widget.active_config_widget_changed.connect(self._effect_config_widget_changed)
        self._effects_list_widget.effect_selected.connect(self._effect_add_button_clicked)
        self._center_scroll_area = QScrollArea()  # TODO replace once widget can scroll based on jog wheel
        self._center_scroll_area.setWidget(self._compilation_widget)
        center_layout.addWidget(self._center_scroll_area)
        self._effect_placement_bar = QSpinBox(center_container)
        self._effect_placement_bar.setMinimum(0)
        self._effect_placement_bar.setMaximum(0)
        self._effect_placement_bar.setVisible(False)
        self._effect_placement_bar.setEnabled(False)
        self._effect_placement_bar.installEventFilter(self)
        center_layout.addWidget(self._effect_placement_bar)
        global_layout.addWidget(center_container)
        self._right_side_container = QSplitter(self)
        self._right_side_container.setOrientation(Qt.Orientation.Vertical)
        self._fixture_list_widget = UniverseTreeBrowserWidget(f.scene.board_configuration)
        self._fixture_list_widget.setParent(self._right_side_container)
        self._fixture_list_widget.itemDoubleClicked.connect(self._fixture_or_group_add_clicked)
        self._right_side_container.addWidget(self._fixture_list_widget)
        self._effect_config_widget_container = QScrollArea()
        self._effect_config_widget_container.setMinimumHeight(50)
        self._right_side_container.addWidget(self._effect_config_widget_container)
        global_layout.addWidget(self._right_side_container)
        self._message_box = QMessageBox(self.parent())

    def _fixture_or_group_add_clicked(self, item: QTreeWidgetItem, column: int):
        if not isinstance(item, AnnotatedTreeWidgetItem):
            return
        if isinstance(item.annotated_data, UsedFixture):
            self._compilation_widget.add_fixture_or_group(item.annotated_data)

    def _effect_add_button_clicked(self, e: Effect):
        self._compilation_widget.load_effect_to_add(e)
        e.set_parent_filter(self._filter)
        avail_slots = self._compilation_widget.get_maximum_slot_counter()
        if avail_slots >= 0:
            self._effect_placement_bar.setMaximum(avail_slots)
            self._effect_placement_bar.setVisible(True)
            self._effect_placement_bar.setEnabled(True)
            self._effect_placement_bar.setValue(0)
            self._effect_placement_bar.selectAll()
            self._effect_placement_bar.setFocus()
        else:
            self._compilation_widget.load_effect_to_add(None)
            self._message_box.setWindowTitle("No matching slots available")
            self._message_box.setText("Currently there are no slots that can accept this effect type.")
            self._message_box.show()

    def eventFilter(self, widget: QWidget, event: QEvent):
        if event.type() == QEvent.KeyPress and widget is self._effect_placement_bar:
            key = event.key()
            if key in [Qt.Key_Return, Qt.Key_Enter]:
                self._compilation_widget.add_effect_to_slot(self._effect_placement_bar.value())
                return True
            if key in [Qt.Key_Escape]:
                self._compilation_widget.load_effect_to_add(None)
                self._effect_placement_bar.setEnabled(False)
                self._effect_placement_bar.setVisible(False)
                self._effect_placement_bar.clearFocus()
                return True
        return False

    def _effect_added(self):
        self._effect_placement_bar.setEnabled(False)
        self._effect_placement_bar.setVisible(False)
        self._effect_placement_bar.clearFocus()

    def _effect_config_widget_changed(self, w: QWidget):
        old_w = self._effect_config_widget_container.widget()
        if w is None:
            return
        w.setParent(self._effect_config_widget_container)
        w.setVisible(True)
        self._effect_config_widget_container.setWidget(w)
        if old_w is not None:
            old_w.setVisible(False)
