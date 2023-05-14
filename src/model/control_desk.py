from abc import ABC, abstractmethod
from Network import NetworkManager
from typing import Tuple
from uuid import uuid4

import proto.Console_pb2


def _generate_unique_id() -> str:
    return str(uuid4())


class DeskColumn(ABC):
    def __init__(self, id: str = None):
        self.id = id if id else _generate_unique_id()
        self.set_text("")
        self.display_color = proto.Console_pb2.lcd_color.white
        self._bottom_display_line_inverted = False
        self._top_display_line_inverted = False

    def update(self):
        """This method updates the state of this column with fish
        """
        # TODO implement
        # TODO generate update message and push it to network manager
        pass

    @abstractmethod
    def _generate_column_message(self) -> proto.Console_pb2.fader_column:
        """This method will be called internally by update in order to obtain the definiton of the column

        Returns:
        The corresponding protobuf message
        """
        pass

    @property
    def display_name(self) -> str:
        return self._upper_text

    @display_name.setter
    def display_name(self, text: str):
        self._lower_text = ""
        self._upper_text = text
        self.update()

    @property
    def bottom_display_line_inverted(self) -> bool:
        return self._bottom_display_line_inverted

    @bottom_display_line_inverted.setter
    def bottom_display_line_inverted(self, state: bool):
        self._bottom_display_line_inverted = state
        self.update()

    @property
    def top_display_line_inverted(self) -> bool:
        return self._top_display_line_inverted

    @top_display_line_inverted.setter
    def top_display_line_inverted(self, state: bool):
        self._top_display_line_inverted = state
        self.update()


class RawDeskColumn(DeskColumn):
    def __init__(self, _id: str = None):
        super().__init__(_id)
        self._fader_position = 0
        self._encoder_position = 0

    def _generate_column_message(self) -> proto.Console_pb2.fader_column:
        # TODO implement
        pass

    @property
    def fader_position(self) -> int:
        return self._fader_position

    @fader_position.setter
    def fader_position(self, position: int):
        self._fader_position = position
        self.update()

    @property
    def encoder_position(self) -> int:
        return self._encoder_position

    @encoder_position.setter
    def encoder_position(self, position: int):
        self._encoder_position = position
        self.update()


class ColorDeskColumn(DeskColumn):
    def __init__(self, _id: str = None):
        super().__init__(_id)
        self._color_h = 0.0
        self._color_s = 0.0
        self._color_i = 0.0

    def _generate_column_message(self) -> proto.Console_pb2.fader_column:
        # TODO implement
        pass

    @property
    def color(self) -> Tuple[float, float, float]:
        return (self._color_h, self._color_s, self._color_i)

    @color.setter
    def color(self, h: float, s: float, i: float):
        self._color_h = h
        self._color_s = s
        self._color_i = i
        self.update()


class FaderBank:
    def __init__(self):
        self.columns = []

    def add_column(self, col: DeskColumn):
        self.columns.append(col)


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
        """Calling this method makes this bank set the active one.
        """
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

    def set_active_bank(self, i: int) -> bool:
        """This method sets the active bank.

        Returns:
        True if the operation was successful. Otherwise False.
        """
        if i < 0 or i >= len(self.banks):
            return False
        self.active_bank = i
        # TODO propagate to fish
        return True
