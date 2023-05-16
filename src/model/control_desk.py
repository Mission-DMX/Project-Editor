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
        self._bottom_display_line_inverted = False
        self._top_display_line_inverted = False
        self._pushed_to_device = False
        self.display_color = proto.Console_pb2.lcd_color.white
        self.display_name = ""

    def update(self) -> bool:
        """This method updates the state of this column with fish
        """
        if not BankSet._fish_connector.is_running or not self._pushed_to_device:
            return False
        msg = self._generate_column_message()
        BankSet._fish_connector.send_update_column_message(msg)
        return True

    @abstractmethod
    def _generate_column_message(self) -> proto.Console_pb2.fader_column:
        """This method will be called internally by update in order to obtain the definiton of the column

        Returns:
        The corresponding protobuf message
        """
        pass

    def _generate_base_column_message(self) -> proto.Console_pb2.fader_column:
        msg = proto.Console_pb2.fader_column(column_id=self.id, display_color=self.display_color)
        msg.upper_display_text = self._upper_text
        msg.lower_display_text = self._lower_text
        msg.top_lcd_row_inverted = self._top_display_line_inverted
        msg.bottom_lcd_row_inverted = self._bottom_display_line_inverted
        return msg

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
        self._select_button_led_active = False
        self._b1_button_led_active = False
        self._b2_button_led_active = False
        self._b3_button_led_active = False

    def _generate_column_message(self) -> proto.Console_pb2.fader_column:
        msg = self._generate_base_column_message()
        msg.raw_data.fader = self._fader_position
        msg.raw_data.rotary_position = self._encoder_position
        msg.raw_data.meter_leds = 0
        msg.raw_data.select = proto.Console_pb2.ButtonState.BS_ACTIVE if self._select_button_led_active else proto.Console_pb2.ButtonState.BS_SET_LED_NOT_ACTIVE
        msg.raw_data.b1 = proto.Console_pb2.ButtonState.BS_ACTIVE if self._b1_button_led_active else proto.Console_pb2.ButtonState.BS_SET_LED_NOT_ACTIVE
        msg.raw_data.b2 = proto.Console_pb2.ButtonState.BS_ACTIVE if self._b2_button_led_active else proto.Console_pb2.ButtonState.BS_SET_LED_NOT_ACTIVE
        msg.raw_data.b3 = proto.Console_pb2.ButtonState.BS_ACTIVE if self._b3_button_led_active else proto.Console_pb2.ButtonState.BS_SET_LED_NOT_ACTIVE
        return msg

    @property
    def fader_position(self) -> int:
        """This method returns the fader position

        Returns:
        fader position as 16 bit unsigned int (between 0 and 65535)
        """
        return self._fader_position

    @fader_position.setter
    def fader_position(self, position: int):
        """Set the fader position. Please keep in mind that the fader positions range from 0 to 65535

        position -- The new position to set
        """
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
        base_msg = self._generate_base_column_message()
        base_msg.plain_color.hue = self._color_h
        base_msg.plain_color.saturation = self._color_s
        base_msg.plain_color.intensity = self._color_i
        return base_msg

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
        self._pushed_to_device = False

    def add_column(self, col: DeskColumn):
        self.columns.append(col)

    def _generate_bank_message(self) -> proto.Console_pb2.add_fader_bank_set.fader_bank:
        msg = proto.Console_pb2.add_fader_bank_set.fader_bank()
        for col in self.columns:
            msg.cols.extend([col._generate_column_message()])
        return msg


class BankSet:

    _fish_connector: NetworkManager = None
    _active_bank_set: str = None
    _seven_seg_data: str = "00          "
    _linked_bank_sets = []

    @staticmethod
    def get_linked_bank_sets():
        return list(BankSet._linked_bank_sets)

    def __init__(self, banks: list[FaderBank], description=None):
        """Construct a bank set object.
        After construction link() needs to be called in order to link the set with the control desk.

        Arguments:
        banks -- The initial list of fader banks
        description -- Optional. A human readable description used in the fader bank editor to identify the set to edit
        """
        self.id = _generate_unique_id()
        self.pushed_to_fish = False
        self.banks = banks
        self.active_bank = 0
        if description:
            self.description = str(description)
        else:
            self.description = "No description"

    def update(self) -> bool:
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
        BankSet._fish_connector.send_add_fader_bank_set_message(new_id, self.active_bank, self.banks)
        if self.pushed_to_fish:
            BankSet._fish_connector.send_fader_bank_set_delete_message(self.id)
        else:
            BankSet._linked_bank_sets.append(self)
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
        self._send_desk_update_message()

    def _send_desk_update_message(self):
        msg = proto.Console_pb2.desk_update()
        msg.selected_column_id = ""  # Do not update the set of selected columns yet
        msg.find_active_on_column_id = ""  # Do not update the column with active 'find fixtrue' feature yet
        msg.selected_bank = self.active_bank
        msg.selected_bank_set = BankSet._active_bank_set
        msg.seven_seg_display_data = BankSet._seven_seg_data
        BankSet._fish_connector.send_desk_update_message(msg)

    def add_bank(self, bank: FaderBank):
        """Update the fader bank on the control desk

        Warning: This operation is expensive and might interrupt the interactions of the user. Add all columns to the
        bank at first. If all you'd like to do is updating a column: call the update function on that column.
        """
        self.columns.append(bank)
        self.update()

    def set_active_bank(self, i: int) -> bool:
        """This method sets the active bank.

        Returns:
        True if the operation was successful. Otherwise False.
        """
        if i < 0 or i >= len(self.banks):
            return False
        self.active_bank = i
        self._send_desk_update_message()
        return True

    def link(self) -> bool:
        return self.update()

    def unlink(self) -> bool:
        """This method removes the bank set from the control desk

        Returns: True on success
        """
        if not self.pushed_to_fish:
            return False
        if not BankSet._fish_connector.is_running:
            return False
        i = 0
        for linked_bank in BankSet._linked_bank_sets:
            if linked_bank.id == self.id:
                found_index = i
                break
            else:
                i += 1
        BankSet._fish_connector.send_fader_bank_set_delete_message(self.id)
        BankSet._linked_bank_sets.pop(found_index)
        return True

    @property
    def is_linked(self) -> bool:
        return self.pushed_to_fish


def set_network_manager(network_manager: NetworkManager):
    BankSet._fish_connector = network_manager


def set_seven_seg_display_content(content: str):
    BankSet._seven_seg_data = content[0:12] + " " * (12 - len(content))
    # TODO send update message

