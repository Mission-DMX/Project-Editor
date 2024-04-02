from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSpacerItem, QSizePolicy, \
    QScrollArea, QLineEdit, QCompleter

from model.virtual_filters.effects_stacks.color_effects import ColorWheelEffect
from model.virtual_filters.effects_stacks.effect import Effect
from model.virtual_filters.effects_stacks.generic_effects import FunctionEffect

EFFECT_LIST = [
    ColorWheelEffect,
    FunctionEffect,
]


class EffectLabel(QWidget):
    button_icon = QIcon.fromTheme("window-new")

    def __init__(self, effect_cls, parent: QWidget):
        super().__init__(parent=parent)
        layout = QHBoxLayout()
        self.setLayout(layout)

        tmp_instance: Effect = effect_cls()
        self.effect_name = tmp_instance.get_human_filter_name()
        self.description = tmp_instance.get_description()
        self._template = effect_cls

        self._label = QLabel(self.effect_name, parent=self)
        layout.addWidget(self._label)

        # TODO do we want to introduce an opportunity here to display an effect icon?

        self._button = QPushButton(self, "Add Effect")
        if self.button_icon:
            self._button.setIcon(self.button_icon)
        layout.addWidget(self._button)
        self.setToolTip(self.description)

    def get_instance(self) -> Effect:
        return self._template()

    def show(self):
        for w in [self, self._label, self._button]:
            w.setVisible(True)

    def hide(self):
        for w in [self, self._label, self._button]:
            w.setVisible(False)


class EffectsListWidget(QWidget):
    def __init__(self, parent: QWidget):
        super().__init__(parent=parent)
        central_layout = QVBoxLayout()
        self.setLayout(central_layout)

        self._search_bar = QLineEdit(parent=self)
        self._search_bar.textChanged.connect(self._update_search)
        central_layout.addWidget(self._search_bar)

        self._effect_container = QScrollArea(parent=self)
        self._scroller = QScrollArea(parent=self)
        container_layout = QVBoxLayout()
        self._effect_container.setLayout(container_layout)
        self._scroller.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self._scroller.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroller.setWidgetResizable(True)
        self._scroller.setWidget(self._effect_container)
        central_layout.addWidget(self._scroller)
        self._effect_widgets: list[EffectLabel] = []
        names: list[str] = []

        for effect_template in EFFECT_LIST:
            w = EffectLabel(effect_template, self._effect_container)
            self._effect_widgets.append(w)
            container_layout.addWidget(w)
            names.append(w.effect_name)
            # TODO introduce category splitters

        self._search_completer = QCompleter(names)
        self._search_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._search_bar.setCompleter(self._search_completer)

        container_layout.addSpacerItem(QSpacerItem(1, 1, QSizePolicy.Minimum, QSizePolicy.Expanding))

    def _update_search(self, new_query_text: str):
        new_query_text = new_query_text.lower()
        for w in self._effect_widgets:
            # TODO introduce category splitters
            if new_query_text in w.effect_name.lower():
                w.show()
            else:
                w.hide()
