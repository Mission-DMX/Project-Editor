from PySide6.QtWidgets import QWidget, QHBoxLayout, QTreeWidget

from model import Filter
from view.show_mode.effect_stacks.effects_compilation_widget import EffectCompilationWidget
from view.show_mode.effect_stacks.effects_list import EffectsListWidget


class EffectsStackEditor(QWidget):

    def __init__(self, f: Filter, parent: QWidget | None):
        super().__init__(parent=parent)
        self._filter = f
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        global_layout = QHBoxLayout()
        self.setLayout(global_layout)
        self._effects_list_widget = EffectsListWidget(self)
        global_layout.addWidget(self._effects_list_widget)
        self._compilation_widget = EffectCompilationWidget(self)
        global_layout.addWidget(self._compilation_widget)
        self._fixture_list_widget = QTreeWidget(self)  # TODO extract fixture browser from show_browser.py to reuse it
        global_layout.addWidget(self._fixture_list_widget)
