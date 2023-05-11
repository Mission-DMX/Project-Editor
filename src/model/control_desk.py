from Network import NetworkManager
from uuid import uuid4


def _generate_unique_id() -> str:
    return str(uuid4())


class DeskColumn:
    def __init__(self, id: str = None):
        self.id = id if id else _generate_unique_id()
        self.text = ""

    def update(self):
        # TODO implement
        pass


class FaderBank:
    def __init__(self):
        self.columns = []


class BankSet:

    _fish_connector: NetworkManager = None
    _active_bank_set: str = None

    def __init__(self, banks: list[FaderBank]):
        self.id = _generate_unique_id()
        self.pushed_to_fish = False
        self.banks = banks
        self.active_bank = 0

    def _update(self) -> bool:
        """push the bank set to fish or update it if required

        Returns:
            True if the bank set was successfully dispatched. Otherwise false
        """
        if not BankSet._fish_connector.is_running:
            return False
        bank_set_size = len(self.banks)
        if bank_set_size < 1:
            return False
        if self.active_bank > bank_set_size - 1:
            self.active_bank = bank_set_size - 1
        new_id = _generate_unique_id()
        BankSet._fish_connector.send_add_fader_bank_message(new_id, self.active_bank, self.banks)
        if self.pushed_to_fish:
            BankSet._fish_connector.send_fader_bank_delete_message(self.id)
        if BankSet._active_bank_set == self.id:
            self.id = new_id
            self.activate()
        elif not BankSet._active_bank_set:
            self.id = new_id
            self.activate()
        else:
            self.id = new_id
        self.pushed_to_fish = True
        return True

    def activate(self):
        BankSet._active_bank_set = self.id
        # TODO send desk_update message
        pass

    def add_bank(self, bank: FaderBank):
        """Update the fader bank on the control desk

        Warning: This operation is expensive and might interrupt the interactions of the user. Add all columns to the
        bank at first. If all you'd like to do is updating a column: call the update function on that column.
        """
        self.columns.append(bank)
        self._update()
