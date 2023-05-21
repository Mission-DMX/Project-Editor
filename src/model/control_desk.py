# coding=utf-8
"""models for X-Touch and also for other connected devices like extenders or joystick"""
from abc import ABC, abstractmethod
from uuid import uuid4

import proto.Console_pb2
from network import NetworkManager
from model.color_hsi import ColorHSI


def _generate_unique_id() -> str:
    return str(uuid4())


class DeskColumn(ABC):
    """This class represents a single column inside a bank.

    This class should not be instantiated directly.
    Instead the implementing classes ColorDeskColumn and RawDeskColumn should be used.

    TODO: Also implement U,UA and A types.
    """

    def __init__(self, uid: str = None):
        self.id = uid if uid else _generate_unique_id()
        self._bottom_display_line_inverted = False
        self._top_display_line_inverted = False
        self._pushed_to_device = False
        self.display_color = proto.Console_pb2.lcd_color.white
        self.display_name = ""

    def update(self) -> bool:
        """This method updates the state of this column with fish"""
        if not BankSet.fish_connector().is_running or not self._pushed_to_device:
            return False
        msg = self._generate_column_message()
        BankSet.fish_connector().send_update_column_message(msg)
        return True

    @abstractmethod
    def _generate_column_message(self) -> proto.Console_pb2.fader_column:
        """This method will be called internally by update in order to obtain the definition of the column

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
        """Top text of the Display"""
        return self._upper_text

    @display_name.setter
    def display_name(self, text: str):
        self._lower_text = ""
        self._upper_text = text
        self.update()

    @property
    def bottom_display_line_inverted(self) -> bool:
        """True if the text foreground and background pixels are inverted."""
        return self._bottom_display_line_inverted

    @bottom_display_line_inverted.setter
    def bottom_display_line_inverted(self, state: bool):
        self._bottom_display_line_inverted = state
        self.update()

    @property
    def top_display_line_inverted(self) -> bool:
        """True if the text foreground and background pixels are inverted."""
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
        msg.raw_data.select = proto.Console_pb2.ButtonState.BS_ACTIVE if self._select_button_led_active else \
            proto.Console_pb2.ButtonState.BS_SET_LED_NOT_ACTIVE
        msg.raw_data.b1 = proto.Console_pb2.ButtonState.BS_ACTIVE if self._b1_button_led_active else \
            proto.Console_pb2.ButtonState.BS_SET_LED_NOT_ACTIVE
        msg.raw_data.b2 = proto.Console_pb2.ButtonState.BS_ACTIVE if self._b2_button_led_active else \
            proto.Console_pb2.ButtonState.BS_SET_LED_NOT_ACTIVE
        msg.raw_data.b3 = proto.Console_pb2.ButtonState.BS_ACTIVE if self._b3_button_led_active else \
            proto.Console_pb2.ButtonState.BS_SET_LED_NOT_ACTIVE
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
        """position of the rotary encoder"""
        return self._encoder_position

    @encoder_position.setter
    def encoder_position(self, position: int):
        self._encoder_position = position
        self.update()


class ColorDeskColumn(DeskColumn):
    def __init__(self, _id: str = None):
        super().__init__(_id)
        self._color: ColorHSI = ColorHSI(0, 0, 0)

    def _generate_column_message(self) -> proto.Console_pb2.fader_column:
        base_msg = self._generate_base_column_message()
        base_msg.plain_color.hue = self.color.hue
        base_msg.plain_color.saturation = self.color.saturation
        base_msg.plain_color.intensity = self.color.intensity
        return base_msg

    @property
    def color(self) -> ColorHSI:
        """color of the colum"""
        return self._color

    @color.setter
    def color(self, color: ColorHSI):
        self._color = color
        self.update()


class FaderBank:
    """Store a bank page of columns the user can switch through.

    Warning: As of the time of this writing, the buttons for scrolling through a bank are not implemented in fish,
     hence the user can only access up to 8 columns.
    """

    def __init__(self):
        self.columns: list[DeskColumn] = []
        self._pushed_to_device = False

    def add_column(self, col: DeskColumn):
        """add a new colum"""
        self.columns.append(col)

    def generate_bank_message(self) -> proto.Console_pb2.add_fader_bank_set.fader_bank:
        """This method computes a proto buf representation of the bank

        Returns:
            proto buf representation
        """
        msg = proto.Console_pb2.add_fader_bank_set.fader_bank()
        for col in self.columns:
            msg.cols.extend([col._generate_column_message()])  # TODO private Methode
        return msg


class BankSet:
    """This class represents a bank set.

    A bank set is a set of banks, the user can switch between at a given time. Multiple bank sets can be linked to fish at the same time but only one may be active at the same time. Only the GUI may specify which bank set is active any given time, except for the event that the active bank set will be unlinked. In this case fish will enable the bank set with the next lower index.
    """

    _fish_connector: NetworkManager = None
    _active_bank_set: str = None
    _seven_seg_data: str = "00          "
    _linked_bank_sets = []

    @classmethod
    def fish_connector(cls) -> NetworkManager:
        """Connector of the Bank"""
        return cls._fish_connector

    @classmethod
    def linked_bank_sets(cls) -> list:
        """This method yields the mutable list of bank sets that are currently loaded in fish.

        This method should only be used by friend classes.
        """
        return cls._linked_bank_sets

    @classmethod
    def active_bank_set(cls) -> str:
        """current bank set"""
        return cls._active_bank_set

    @staticmethod
    def get_linked_bank_sets() -> list["BankSet"]:
        """This method returns a copy of the linked bank sets, save to be used by non friend classes."""
        return list(BankSet._linked_bank_sets)

    def __init__(self, banks: list[FaderBank], description=None):
        """Construct a bank set object.
        After construction link() needs to be called in order to link the set with the control desk.

        Arguments:
        banks -- The initial list of fader banks
        description -- Optional. A human-readable description used in the fader bank editor to identify the set to edit
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
        text = "Bank: " + self.description
        BankSet._seven_seg_data = (str(self.active_bank % 100) if self.active_bank > 9 else "0" +
                                   str(self.active_bank)) + text[-10:] + (" " * (10 - len(text)))
        self._send_desk_update_message()

    def _send_desk_update_message(self):
        msg = proto.Console_pb2.desk_update()
        msg.selected_column_id = ""  # Do not update the set of selected columns yet
        msg.find_active_on_column_id = ""  # Do not update the column with active 'find fixture' feature yet
        msg.selected_bank = self.active_bank
        msg.selected_bank_set = BankSet._active_bank_set
        msg.seven_seg_display_data = BankSet._seven_seg_data
        BankSet._fish_connector.send_desk_update_message(msg)

    def add_bank(self, bank: FaderBank):
        """Update the fader bank on the control desk

        Warning: This operation is expensive and might interrupt the interactions of the user. Add all columns to the
        bank at first. If all you'd like to do is updating a column: call the update function on that column.
        """
        self.columns.append(bank)  # TODO ein BankSet has no columns attribute
        self.update()

    def set_active_bank(self, i: int) -> bool:
        """This method sets the active bank.

        Returns:
        True if the operation was successful, Otherwise False.
        """
        if i < 0 or i >= len(self.banks):
            return False
        self.active_bank = i
        text = self.description
        BankSet._seven_seg_data = (str(i % 100) if i > 9 else "0" + str(i)) + text[-10:] + (" " * (10 - len(text)))
        self._send_desk_update_message()
        return True

    def link(self) -> bool:
        """Load the bank set to fish.

        If there was no bank set linked before this bank set might become the active one immediately."""
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
        BankSet._linked_bank_sets.pop(found_index)  # TODO found index koente leer sein
        return True

    @property
    def is_linked(self) -> bool:
        """Returns True if the bank set is loaded to fish."""
        return self.pushed_to_fish


def set_network_manager(network_manager: NetworkManager):
    """Set the network manager instance to be used by all bank sets and subsequent banks and columns."""
    BankSet._fish_connector = network_manager


def set_seven_seg_display_content(content: str):
    """Set the content of the 7seg displays of connected X-Touch controllers.

    Fish will truncate any text longer than 12 chars and
    only guarantees the correct display of hexadecimal characters due to the limitations of seven segment displays.
    """
    BankSet._seven_seg_data = content[0:12] + " " * (12 - len(content))
    # TODO send update message


def commit_all_bank_sets():
    """This method calls update on all linked columns.

    This is useful in the event of a reconnect to fish as the state of fish is unknown at this point in time.
    """
    bank_set_for_activation = None
    for bs in BankSet.linked_bank_sets():
        bs.update()
        if bs.id == BankSet.active_bank_set():
            bank_set_for_activation = bs
    if bank_set_for_activation:
        bank_set_for_activation.activate()
