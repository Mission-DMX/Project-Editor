from PySide6.QtWidgets import QWidget, QHBoxLayout, QTreeWidgetItem

from controller.ofl.fixture import UsedFixture
from model import Filter
from model.virtual_filters import EffectsStack
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
        self._compilation_widget = EffectCompilationWidget(f, self)
        self._effects_list_widget.effect_selected.connect(self._compilation_widget.add_effect)
        global_layout.addWidget(self._compilation_widget)
        self._fixture_list_widget = UniverseTreeBrowserWidget(f.scene.board_configuration)
        self._fixture_list_widget.setParent(self)
        self._fixture_list_widget.itemDoubleClicked.connect(self._fixture_or_group_add_clicked)
        global_layout.addWidget(self._fixture_list_widget)

    def _fixture_or_group_add_clicked(self, item: QTreeWidgetItem, column: int):
        if not isinstance(item, AnnotatedTreeWidgetItem):
            return
        if isinstance(item.annotated_data, UsedFixture):
            self._compilation_widget.add_fixture_or_group(item.annotated_data)
