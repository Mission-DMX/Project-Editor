from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QToolBar, QListWidget, QListWidgetItem

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

        self._bank_edit_widget = _BankEditWidget("Columns in selected Bank (Up to eight)")  # TODO

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
        self._bank_edit_widget.bank = item._bank


class _BankItem(QListWidgetItem):
    def __init__(self, bank: FaderBank, index: int):
        super().__init__(str(index))
        self._bank = bank


class _BankEditWidget(QLabel):
    @property
    def bank(self) -> FaderBank:
        return self._bank

    @bank.setter
    def bank(self, bank: FaderBank):
        self._bank = bank
