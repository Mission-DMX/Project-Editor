from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QEnterEvent
from PySide6.QtWidgets import QWidget, QHBoxLayout, QTreeWidgetItem, QVBoxLayout, QSpinBox, QMessageBox

from controller.ofl.fixture import UsedFixture
from model import Filter
from model.virtual_filters import EffectsStack
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
        self._effects_list_widget.effect_selected.connect(self._effect_add_button_clicked)
        center_layout.addWidget(self._compilation_widget)
        self._effect_placement_bar = QSpinBox(center_container)
        self._effect_placement_bar.setMinimum(0)
        self._effect_placement_bar.setMaximum(0)
        self._effect_placement_bar.setVisible(False)
        self._effect_placement_bar.setEnabled(False)
        self._effect_placement_bar.installEventFilter(self)
        center_layout.addWidget(self._effect_placement_bar)
        global_layout.addWidget(center_container)
        self._fixture_list_widget = UniverseTreeBrowserWidget(f.scene.board_configuration)
        self._fixture_list_widget.setParent(self)
        self._fixture_list_widget.itemDoubleClicked.connect(self._fixture_or_group_add_clicked)
        global_layout.addWidget(self._fixture_list_widget)
        self._message_box = QMessageBox(self.parent())

    def _fixture_or_group_add_clicked(self, item: QTreeWidgetItem, column: int):
        if not isinstance(item, AnnotatedTreeWidgetItem):
            return
        if isinstance(item.annotated_data, UsedFixture):
            self._compilation_widget.add_fixture_or_group(item.annotated_data)

    def _effect_add_button_clicked(self, e: Effect):
        self._compilation_widget.load_effect_to_add(e)
        avail_slots = self._compilation_widget.get_maximum_slot_counter()
        if avail_slots > 0:
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
        return False

    def _effect_added(self):
        self._effect_placement_bar.setEnabled(False)
        self._effect_placement_bar.setVisible(False)
        self._effect_placement_bar.clearFocus()
