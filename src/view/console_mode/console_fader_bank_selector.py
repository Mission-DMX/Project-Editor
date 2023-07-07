from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QWidget

from model.control_desk import BankSet, RawDeskColumn, FaderBank


class ConsoleFaderBankSelectorWidget(QComboBox):
    def __init__(self, bank_set: BankSet, display_text: str, parent: QWidget = None):
        super().__init__(parent)
        self._bank_set = bank_set
        self.setEditable(False)
        self.insertItem(0, "None")
        self.insertItem(1, "New Page")
        self.insertSeparator(2)
        self.setCurrentIndex(0)
        self.currentIndexChanged.connect(self._selection_changed)
        self.fader_value_changed = Signal(int)
        self.fader_value_changed.connect(self._update_fader_position)
        self._fader: RawDeskColumn | None = None
        self._latest_hardware_position_update = -1
        self._latest_ui_position_update = -1
        self._bank_index = -1
        self._display_text = display_text

    def _insert_fader_column(self):
        if self._fader:
            self._unlink_fader()
        self._fader = RawDeskColumn()
        self._fader.data_changed.connect(self._data_changed_from_fader)
        self._fader.fader_position = min(self._latest_ui_position_update, 0)
        self._fader.display_name = self._display_text
        self._bank_index = self.currentIndex() - 3
        if len(self._bank_set.banks) <= self._bank_index:
            self._bank_set.add_bank(FaderBank())
        self._bank_set.banks[self._bank_index].add_column(self._fader)
        self._bank_set.update()

    def _selection_changed(self, new_index):
        if new_index == 0 and self._fader:
            self._unlink_fader()
        elif new_index == 1:
            self.insertItem(self.count(), "Bank " + str(self.count() - 3))
        elif new_index > 2:
            self._insert_fader_column()

    def _unlink_fader(self):
        self._bank_set.banks[self._bank_index].remove_column(self._fader)
        self._fader = None

    def _data_changed_from_fader(self):
        if self._fader:
            new_value = round((self._fader.fader_position * 256) / 65536)
            self._latest_hardware_position_update = new_value
            self.fader_value_changed.emit(new_value)

    def _update_fader_position(self, new_value):
        self._latest_ui_position_update = new_value
        if self._fader and new_value != self._latest_hardware_position_update:
            self._fader.fader_position = round((new_value * 65536) / 256)
