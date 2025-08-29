"""Contains ConsoleFaderBankSelectorWidget."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QWidget

from model.control_desk import BankSet, FaderBank, RawDeskColumn


class ConsoleFaderBankSelectorWidget(QComboBox):
    """Widget to select a fader bank."""

    fader_value_changed = Signal(int)

    def __init__(
        self,
        bank_set: BankSet,
        display_text: str,
        parent: QWidget = None,
        bank_set_control_list: list[QWidget] | None = None,
    ) -> None:
        """Initialize the widget."""
        super().__init__(parent)
        if bank_set_control_list is None:
            bank_set_control_list = []
        self._bank_set = bank_set
        self.setEditable(False)
        self.insertItem(0, "None")
        self.insertItem(1, "New Page")
        self.insertSeparator(2)
        self.setCurrentIndex(0)
        self.currentIndexChanged.connect(self._selection_changed)
        self.fader_value_changed.connect(self._update_fader_position)
        self._fader: RawDeskColumn | None = None
        self._latest_hardware_position_update = -1
        self._latest_ui_position_update = -1
        self._bank_index = -1
        self._display_text = display_text
        self._bank_set_control_list = bank_set_control_list
        self._bank_set_control_list.append(self)
        self._skip_next_update = False

    def insert_fader_column(self, force_bank_index: int | None = None) -> None:
        """Add a new fader column.

        Args:
            force_bank_index: Index of fader column to insert. If None: go to the end of the bank.

        """
        self._skip_next_update = True
        if self._fader:
            self._unlink_fader()
        self._fader = RawDeskColumn()
        self._fader.data_changed_callback = self._data_changed_from_fader
        self._fader.fader_position = min(self._latest_ui_position_update, 0)
        self._fader.display_name = self._display_text
        self._bank_index = self.currentIndex() - 3 if force_bank_index is None else force_bank_index
        if len(self._bank_set.banks) <= self._bank_index:
            self._bank_set.add_bank(FaderBank())
        self._bank_set.banks[self._bank_index].add_column(self._fader)
        self._bank_set.update()

    def _selection_changed(self, new_index: int) -> None:
        if new_index == 0 and self._fader:
            self._unlink_fader()
        elif new_index == 1:
            name = str(self.count() - 3) + " Bank"
            for combo_box in self._bank_set_control_list:
                combo_box.insertItem(self.count(), name)
            if self._bank_index > -1:
                self.setCurrentIndex(self._bank_index + 3)
            else:
                self.setCurrentIndex(0)
        elif new_index > 2:
            self.insert_fader_column()
        self._bank_set.push_messages_now()

    def _unlink_fader(self) -> None:
        self._bank_set.banks[self._bank_index].remove_column(self._fader)
        self._fader = None

    def _data_changed_from_fader(self) -> None:
        if self._fader:
            new_value = round((self._fader.fader_position * 256) / 65536)
            self._latest_hardware_position_update = new_value
            self.fader_value_changed.emit(new_value)

    def _update_fader_position(self, new_value: int) -> None:
        if self._skip_next_update:
            new_value = self._latest_ui_position_update
            self._skip_next_update = False
        if self._fader and new_value != self._latest_hardware_position_update:
            self._latest_ui_position_update = new_value
            self._fader.fader_position = round((new_value * 65536) / 256)
            self._bank_set.push_messages_now()
