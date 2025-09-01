"""This file implements the list widget for effects. Register your effect inside the EFFECT_LIST widget.
Usage: The key indicates the category of the effect and the list all containing effects."""

from typing import override

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QIcon, QPainter, QPaintEvent
from PySide6.QtWidgets import (
    QCompleter,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from model.virtual_filters.effects_stacks.effect import Effect
from model.virtual_filters.effects_stacks.effects.color_effects import ColorWheelEffect
from model.virtual_filters.effects_stacks.effects.fader_input_effects import ColorInputEffect
from model.virtual_filters.effects_stacks.effects.generic_effects import FunctionEffect

EFFECT_LIST: dict[str, list[type[Effect]]] = {
    "colors:": [ColorWheelEffect],
    "animations": [FunctionEffect],
    "fader-inputs": [ColorInputEffect],
}

PRESET_LIST: list[tuple[str, str]] = []


# TODO implement a way to load user defined presets. A preset is a tuple of a name and a string that reassembles the
#  filter configuration to be loaded. It will call the effect factory in case of instantiation and loads that one inside
#  the slot instead of a fresh filter object. The json file containing the presets should first be loaded from the
#  resources folder and from the users home directory afterwards. Therefore it is about time to introduce a file that
#  handles stuff written to the users directory, including but not limited to, non-show settings of the editor


class _EffectSeparator(QWidget):
    """This widget provides a separator between effect categories."""

    def __init__(self, parent: QWidget, text: str) -> None:
        super().__init__(parent=parent)
        self._children: list[QWidget] = []
        self._text = text
        self.setFont(self.font())

    @override
    def setFont(self, font: QFont) -> None:
        super().setFont(font)
        fm = self.fontMetrics()
        self.setMinimumHeight(fm.height() + 2)
        self.setMinimumWidth(fm.horizontalAdvance(self._text) + 10)

    def add_child(self, c: QWidget) -> None:
        self._children.append(c)
        self.update_visibility()

    def update_visibility(self) -> None:
        visible = False
        for c in self._children:
            visible |= not c.isHidden()
        self.setVisible(visible)

    @override
    def paintEvent(self, event: QPaintEvent) -> None:
        p = QPainter(self)
        if self.isVisible():
            fm = self.fontMetrics()
            text_height = fm.height()
            text_space = fm.horizontalAdvance(" ")
            text_width = fm.horizontalAdvance(self._text)
            p.drawText(int(text_space / 2), text_height + 1, self._text)
            p.setBrush(QBrush(QColor.fromRgb(0xCC, 0xCC, 0xCC)))
            p.drawLine(int(text_space * 1.5 + text_width), int(text_height * 0.75),
                       int(self.width() - text_space / 2), int(text_height * 0.75))
        p.end()


class _EffectLabel(QWidget):
    """This widget displays the name of the effect and provides a button to add it."""

    button_icon = QIcon.fromTheme("window-new")

    def __init__(self, effect_cls: type[Effect], parent: QWidget, separator: _EffectSeparator,
                 list_widget: "EffectsListWidget") -> None:
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
        self._button.clicked.connect(self.add_effect)
        layout.addWidget(self._button)
        self.setToolTip(self.description)
        self._separator = separator
        separator.add_child(self)
        self._list_widget = list_widget

    def show(self) -> None:
        for w in [self, self._label, self._button]:
            w.setVisible(True)
        self._separator.update_visibility()

    def hide(self) -> None:
        for w in [self, self._label, self._button]:
            w.setVisible(False)
        self._separator.update_visibility()

    def add_effect(self) -> None:
        self._list_widget.effect_selected.emit(self._template())


class EffectsListWidget(QWidget):
    """
    This widget displays all effects in a searchable manner. It furthermore enables the user to select one.
    """

    effect_selected = Signal(Effect)

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent=parent)
        central_layout = QVBoxLayout()
        self.setLayout(central_layout)

        self._search_bar = QLineEdit(parent=self)
        self._search_bar.textChanged.connect(self._update_search)
        self._search_bar.setPlaceholderText("Search Effects")
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
        self._effect_widgets: list[_EffectLabel] = []
        names: list[str] = []

        for collection_name, effect_collection in EFFECT_LIST.items():
            sep = _EffectSeparator(self._effect_container, collection_name)
            container_layout.addWidget(sep)
            for effect_template in effect_collection:
                w = _EffectLabel(effect_template, self._effect_container, sep, self)
                self._effect_widgets.append(w)
                container_layout.addWidget(w)
                names.append(w.effect_name)

        self._search_completer = QCompleter(names)
        self._search_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._search_bar.setCompleter(self._search_completer)

        container_layout.addSpacerItem(QSpacerItem(1, 1, QSizePolicy.Minimum, QSizePolicy.Expanding))
        self.setMaximumWidth(400)

    def _update_search(self, new_query_text: str) -> None:
        new_query_text = new_query_text.lower()
        for w in self._effect_widgets:
            # TODO introduce category splitters
            if new_query_text in w.effect_name.lower():
                w.show()
            else:
                w.hide()
