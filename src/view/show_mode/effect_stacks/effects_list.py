from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QPaintEvent, QPainter, QBrush, QColor
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSpacerItem, QSizePolicy, \
    QScrollArea, QLineEdit, QCompleter, QFrame

from model.virtual_filters.effects_stacks.color_effects import ColorWheelEffect
from model.virtual_filters.effects_stacks.effect import Effect
from model.virtual_filters.effects_stacks.generic_effects import FunctionEffect

EFFECT_LIST = {
    "colors:": [ColorWheelEffect],
    "animations": [FunctionEffect],
}


class _EffectSeparator(QWidget):
    def __init__(self, parent: QWidget, text: str):
        super().__init__(parent=parent)
        self._children: list[QWidget] = []
        self._text = text
        self.setFont(self.font())

    def setFont(self, arg__1):
        super().setFont(arg__1)
        fm = self.fontMetrics()
        self.setMinimumHeight(fm.height() + 2)
        self.setMinimumWidth(fm.horizontalAdvance(self._text) + 10)

    def add_child(self, c: QWidget):
        self._children.append(c)
        self.update_visibility()

    def update_visibility(self):
        visible = False
        for c in self._children:
            visible |= not c.isHidden()
        self.setVisible(visible)

    def paintEvent(self, event: QPaintEvent):
        p = QPainter(self)
        if self.isVisible():
            fm = self.fontMetrics()
            text_height = fm.height()
            text_space = fm.horizontalAdvance(' ')
            text_width = fm.horizontalAdvance(self._text)
            p.drawText(int(text_space / 2), text_height + 1, self._text)
            p.setBrush(QBrush(QColor.fromRgb(0xCC, 0xCC, 0xCC)))
            p.drawLine(int(text_space * 1.5 + text_width), int(text_height * 0.75),
                       int(self.width() - text_space / 2), int(text_height * 0.75))
        p.end()


class _EffectLabel(QWidget):
    button_icon = QIcon.fromTheme("window-new")

    def __init__(self, effect_cls, parent: QWidget, separator: _EffectSeparator, list_widget: "EffectsListWidget"):
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

    def show(self):
        for w in [self, self._label, self._button]:
            w.setVisible(True)
        self._separator.update_visibility()

    def hide(self):
        for w in [self, self._label, self._button]:
            w.setVisible(False)
        self._separator.update_visibility()

    def add_effect(self):
        self._list_widget.effect_selected.emit(self._template())


class EffectsListWidget(QWidget):

    effect_selected = Signal(Effect)

    def __init__(self, parent: QWidget):
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

    def _update_search(self, new_query_text: str):
        new_query_text = new_query_text.lower()
        for w in self._effect_widgets:
            # TODO introduce category splitters
            if new_query_text in w.effect_name.lower():
                w.show()
            else:
                w.hide()