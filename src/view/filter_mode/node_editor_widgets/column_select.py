from PySide6.QtWidgets import QWidget, QTreeWidget, QTreeWidgetItem

from model.control_desk import BankSet, RawDeskColumn, ColorDeskColumn


class ColumnSelect(QTreeWidget):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent=parent)
        self.setColumnCount(2)
        self.clear()
        for bank_set in BankSet.get_linked_bank_sets():
            set_item = QTreeWidgetItem()
            set_item.setText(0, bank_set.description if bank_set.description else bank_set.id)
            set_item.setText(1, str(bank_set.description))
            set_item.setData(0, 0, bank_set)
            i: int = 0
            for bank in bank_set.banks:
                bank_item = QTreeWidgetItem()
                bank_item.setText(0, str(i))
                bank_item.setText(1, "")
                for column in bank.columns:
                    column_item = QTreeWidgetItem()
                    column_item.setText(0, str(column.id))
                    if isinstance(column, RawDeskColumn):
                        column_type_str = "RAW"
                    elif isinstance(column, ColorDeskColumn):
                        column_type_str = "Color HSI"
                    else:
                        column_type_str = "?"
                    column_item.setText(1, column_type_str)
                    column_item.setData(0, 0, column)
                    bank_item.addChild(column_item)
                    self._selected_item = column_item
                set_item.addChild(set_item)
                i += 1
            self.insertTopLevelItem(0, set_item)
        self.itemSelectionChanged.connect()

    def _get_configuration(self) -> dict[str, str]:
        data = {
            "column_id": self._selected_item.data(0, 0).id,
            "set_id": self._selected_item.parent().parent().data(0, 0).id
        }
        return data

    def _selection_changed_handler(self, *args):
        item = self.selectedItems()[0]
        if item.text(1):
            self._selected_item = item
