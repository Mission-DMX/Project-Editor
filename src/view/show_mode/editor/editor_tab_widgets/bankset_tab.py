from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QWidget, QVBoxLayout, QToolBar, QListWidget, QListWidgetItem, QHBoxLayout, QLineEdit, \
    QCheckBox

from model.control_desk import BankSet, FaderBank


class BankSetTabWidget(QWidget):
    def __init__(self, bankset: BankSet):
        super().__init__()
        self._bankset = bankset

        layout = QVBoxLayout()
        self._tool_bar = QToolBar()
        self._tool_bar.addAction(QIcon.fromTheme("list-add"), "Add Bank", lambda: self._add_bank())

        self._bank_list = QListWidget(self)
        self._bank_list.itemClicked.connect(self._select_bank_to_edit)

        self._bank_edit_widget = _BankEditWidget()

        layout.addWidget(self._tool_bar)  # TODO do we want the list view to be next to the tool bar?
        layout.addWidget(self._bank_list)
        layout.addWidget(self._bank_edit_widget)
        self.setLayout(layout)

    @property
    def bankset(self) -> BankSet:
        return self._bankset

    def _add_bank(self):
        b = FaderBank()
        self._bank_list.addItem(_BankItem(b, self._bank_list.count()))
        self._bankset.add_bank(b)

    def _select_bank_to_edit(self, item: QListWidgetItem):
        if not isinstance(item, _BankItem):
            return
        self._bank_edit_widget.bank = item.bank


class _BankItem(QListWidgetItem):
    def __init__(self, bank: FaderBank, index: int):
        super().__init__(str(index))
        self._bank = bank

    @property
    def bank(self) -> FaderBank:
        return self._bank

    @bank.setter
    def bank(self, b: FaderBank):
        self._bank = b


class _BankEditWidget(QWidget):

    def __init__(self):
        self._bank: FaderBank | None = None
        layout = QHBoxLayout()

        self._text_widgets: list[QLineEdit] = []
        self._top_inverted_widgets: list[QCheckBox] = []
        self._bottom_inverted_widgets: list[QCheckBox] = []
        # TODO add type selection combo box
        # TODO add type specific widgets

        for i in range(8):
            column_widget = QWidget(self)
            column_layout = QVBoxLayout()
            column_widget.setLayout(column_layout)
            self._text_widgets[i] = QLineEdit(column_widget)
            self._text_widgets[i].textChanged.connect(lambda i=i: self._display_text_field_changed(i))
            column_layout.addWidget(self._text_widgets[i])
            # TODO add remaining widgets
            # TODO add border around column
        self.setLayout(layout)

    @property
    def bank(self) -> FaderBank:
        return self._bank

    @bank.setter
    def bank(self, bank: FaderBank):
        self._bank = bank

    def _display_text_field_changed(self, index: int):
        if self._bank:
            self._bank.columns[index].display_name = self._text_widgets[index].text()
