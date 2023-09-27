from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QWidget, QVBoxLayout, QToolBar, QListWidget, QListWidgetItem, QHBoxLayout, QLineEdit, \
    QCheckBox, QGroupBox, QLabel, QComboBox

from model.control_desk import BankSet, FaderBank, ColorDeskColumn, RawDeskColumn


class BankSetTabWidget(QWidget):
    def __init__(self, parent: QWidget, bankset: BankSet):
        super().__init__(parent)
        self._bankset = bankset

        layout = QVBoxLayout()
        self._tool_bar = QToolBar()
        self._tool_bar.addAction(QIcon.fromTheme("document-new"), "Add Bank", lambda: self._add_bank())
        self._tool_bar.addAction(QIcon.fromTheme("list-add"), "Add Column to current Bank", lambda: self._add_column())
        self._new_column_type_cbox = QComboBox()
        self._new_column_type_cbox.insertItems(0, ["Numbers", "Color"])
        self._new_column_type_cbox.setCurrentIndex(1)
        self._new_column_type_cbox.setEnabled(not self._bankset.is_empty)
        self._tool_bar.addWidget(self._new_column_type_cbox)

        self._bank_list = QListWidget(self)
        self._bank_list.itemClicked.connect(self._select_bank_to_edit)

        self._bank_edit_widget = _BankEditWidget(self)

        layout.addWidget(self._tool_bar)  # TODO do we want the list view to be next to the tool bar?
        layout.addWidget(self._bank_list)
        layout.addWidget(self._bank_edit_widget)
        self.setLayout(layout)

    @property
    def bankset(self) -> BankSet:
        return self._bankset

    def _add_bank(self):
        was_empty = self._bankset.is_empty
        b = FaderBank()
        self._bank_list.addItem(_BankItem(b, self._bank_list.count()))
        self._bankset.add_bank(b)
        if was_empty:
            self._new_column_type_cbox.setEnabled(True)
            self._bank_list.setCurrentRow(0)

    def _select_bank_to_edit(self, item: QListWidgetItem):
        if not isinstance(item, _BankItem):
            return
        self._bank_edit_widget.bank = item.bank

    def _add_column(self):
        for item in self._bank_list.selectedItems():
            if not isinstance(item, _BankItem):
                continue
            if len(item.bank.columns) > 7:
                continue
            if self._new_column_type_cbox.currentText() == "Color":
                col = ColorDeskColumn()
            else:
                col = RawDeskColumn()
            item.bank.columns.append(col)
            self._bank_edit_widget.refresh_column_count()
            break


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

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self._bank: FaderBank | None = None
        layout = QVBoxLayout()

        self._text_widgets: list[QLineEdit] = []
        self._top_inverted_widgets: list[QCheckBox] = []
        self._bottom_inverted_widgets: list[QCheckBox] = []
        # TODO add type selection combo box
        # TODO add type specific widgets

        column_edit_row_container = QWidget(self)
        column_edit_row_container_layout = QHBoxLayout()

        for i in range(8):
            column_widget = QGroupBox(self, "Column " + str(i))
            column_widget.setMinimumWidth(100)
            column_widget.setMinimumHeight(200)
            column_layout = QVBoxLayout()
            column_widget.setLayout(column_layout)
            column_layout.addWidget(QLabel("Display Text:"))
            self._text_widgets.append(QLineEdit(column_widget))
            self._text_widgets[i].textChanged.connect(
                lambda text, ci=i: self._display_text_field_changed(ci, text)
            )
            column_layout.addWidget(self._text_widgets[i])
            self._top_inverted_widgets.append(QCheckBox("Top line inverted", column_widget))
            self._top_inverted_widgets[i].stateChanged.connect(
                lambda checked, ci=i: self._top_inverted_changed(ci, checked)
            )
            column_layout.addWidget(self._top_inverted_widgets[i])
            self._bottom_inverted_widgets.append(QCheckBox("Bottom line inverted", column_widget))
            self._bottom_inverted_widgets[i].stateChanged.connect(
                lambda checked, ci=i: self._bottom_inverted_changed(ci, checked)
            )
            column_layout.addWidget(self._bottom_inverted_widgets[i])
            # TODO add remaining widgets
            column_edit_row_container_layout.addWidget(column_widget)
        column_edit_row_container.setLayout(column_edit_row_container_layout)
        layout.addWidget(column_edit_row_container)
        self.setLayout(layout)

        self.bank = None

    @property
    def bank(self) -> FaderBank:
        return self._bank

    @bank.setter
    def bank(self, bank: FaderBank | None):
        self._bank = bank
        self.refresh_column_count()

    def refresh_column_count(self):
        if self._bank:
            number_of_columns = len(self._bank.columns)
        else:
            number_of_columns = 0
        for i in range(len(self._text_widgets)):
            column_enabled = i < number_of_columns
            self._text_widgets[i].setEnabled(column_enabled)
            self._top_inverted_widgets[i].setEnabled(column_enabled)
            self._bottom_inverted_widgets[i].setEnabled(column_enabled)
            if column_enabled:
                current_column = self._bank.columns[i]
                self._text_widgets[i].setText(current_column.display_name)
                self._top_inverted_widgets[i].setChecked(current_column.top_display_line_inverted)
                self._bottom_inverted_widgets[i].setChecked(current_column.bottom_display_line_inverted)
            else:
                self._text_widgets[i].setText("")
                self._top_inverted_widgets[i].setChecked(False)
                self._bottom_inverted_widgets[i].setChecked(False)

    def _display_text_field_changed(self, index: int, text: str):
        if self._bank:
            self._bank.columns[index].display_name = self._text_widgets[index].text()

    def _top_inverted_changed(self, index: int, checked: bool):
        if self._bank:
            self._bank.columns[index].top_display_line_inverted = self._top_inverted_widgets[index].isChecked()

    def _bottom_inverted_changed(self, index: int, checked: bool):
        if self._bank:
            self._bank.columns[index].bottom_display_line_inverted = self._bottom_inverted_widgets[index].isChecked()
