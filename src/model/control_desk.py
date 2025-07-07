"""models for X-Touch and also for other connected devices like extenders or joystick"""
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from uuid import uuid4

import proto.Console_pb2
from model.broadcaster import Broadcaster
from model.color_hsi import ColorHSI

if TYPE_CHECKING:
    from controller.network import NetworkManager

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
        self.bank_set: BankSet | None = None
        self._bottom_display_line_inverted = False
        self._top_display_line_inverted = False
        self._pushed_to_device = False
        self.display_color = proto.Console_pb2.lcd_color.white
        self._lower_text = ""
        self._upper_text = ""
        self.data_changed_callback = None

    def copy_base(self, dc: "DeskColumn"):
        dc._bottom_display_line_inverted = self._bottom_display_line_inverted
        dc._top_display_line_inverted = self._top_display_line_inverted
        dc.display_color = self.display_color
        dc._lower_text = self._lower_text
        dc._upper_text = self._upper_text

    @abstractmethod
    def copy(self) -> "DeskColumn":
        pass

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

    @abstractmethod
    def update_from_message(self, message: proto.Console_pb2.fader_column):
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
    def copy(self) -> "DeskColumn":
        base_dc = RawDeskColumn(self.id)
        self.copy_base(base_dc)
        base_dc._fader_position = self._fader_position
        base_dc._encoder_position = self._encoder_position
        base_dc._select_button_led_active = self._select_button_led_active
        base_dc._b1_button_led_active = self._b1_button_led_active
        base_dc._b2_button_led_active = self._b2_button_led_active
        base_dc._b3_button_led_active = self._b3_button_led_active
        base_dc._secondary_text_line = self._secondary_text_line
        return base_dc

    def __init__(self, _id: str = None):
        super().__init__(_id)
        self._fader_position = 0
        self._encoder_position = 0
        self._select_button_led_active = False
        self._b1_button_led_active = False
        self._b2_button_led_active = False
        self._b3_button_led_active = False
        self._secondary_text_line: str = ""

    def _generate_column_message(self) -> proto.Console_pb2.fader_column:
        msg = self._generate_base_column_message()
        msg.raw_data.fader = self._fader_position
        msg.raw_data.rotary_position = self._encoder_position
        msg.raw_data.meter_leds = 0
        msg.raw_data.select = proto.Console_pb2.ButtonState.BS_ACTIVE \
            if self._select_button_led_active else proto.Console_pb2.ButtonState.BS_SET_LED_NOT_ACTIVE
        msg.raw_data.b1 = proto.Console_pb2.ButtonState.BS_ACTIVE \
            if self._b1_button_led_active else proto.Console_pb2.ButtonState.BS_SET_LED_NOT_ACTIVE
        msg.raw_data.b2 = proto.Console_pb2.ButtonState.BS_ACTIVE \
            if self._b2_button_led_active else proto.Console_pb2.ButtonState.BS_SET_LED_NOT_ACTIVE
        msg.raw_data.b3 = proto.Console_pb2.ButtonState.BS_ACTIVE \
            if self._b3_button_led_active else proto.Console_pb2.ButtonState.BS_SET_LED_NOT_ACTIVE
        msg.lower_display_text = self._secondary_text_line
        return msg

    def update_from_message(self, message: proto.Console_pb2.fader_column):
        if not message.raw_data:
            return
        self._fader_position = message.raw_data.fader
        self._encoder_position = message.raw_data.rotary_position  # TODO implement buttons once implemented in fish
        if self.data_changed_callback:
            self.data_changed_callback()

    @property
    def secondary_text_line(self) -> str:
        """This method returns the currently used second text line

        Returns:
            The text as a string
        """
        return self._secondary_text_line

    @secondary_text_line.setter
    def secondary_text_line(self, new_value: str | None):
        """This method sets the secondary text line.

        new_value -- The text to set
        """
        if new_value:
            self._secondary_text_line = str(new_value)
        else:
            self._secondary_text_line = ""
        self.update()

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
        if self._fader_position == position:
            return
        self._fader_position = position
        self._fader_position = max(self._fader_position, 0)
        self._fader_position = min(self._fader_position, 65535)
        self.update()

    @property
    def encoder_position(self) -> int:
        """position of the rotary encoder"""
        return self._encoder_position

    @encoder_position.setter
    def encoder_position(self, position: int):
        if position == self._encoder_position:
            return
        self._encoder_position = position
        self.update()


class ColorDeskColumn(DeskColumn):
    def copy(self) -> "DeskColumn":
        base_dc = ColorDeskColumn(self.id)
        self.copy_base(base_dc)
        base_dc._color = self._color.copy()
        return base_dc

    def __init__(self, _id: str = None):
        super().__init__(_id)
        self._color: ColorHSI = ColorHSI(0.0, 0.0, 0.0)

    def _generate_column_message(self) -> proto.Console_pb2.fader_column:
        base_msg = self._generate_base_column_message()
        base_msg.plain_color.hue = self.color.hue
        base_msg.plain_color.saturation = self.color.saturation
        base_msg.plain_color.intensity = self.color.intensity
        return base_msg

    def update_from_message(self, message: proto.Console_pb2.fader_column):
        if not message.plain_color:
            return
        self._color = ColorHSI(message.plain_color.hue, message.plain_color.saturation, message.plain_color.intensity)
        if self.data_changed_callback:
            self.data_changed_callback()

    @property
    def color(self) -> ColorHSI:
        """color of the colum"""
        return self._color

    @color.setter
    def color(self, color: ColorHSI):
        if color == self._color:
            return
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

    @property
    def pushed_to_device(self) -> bool:
        """property for pushed_to_device"""
        return self._pushed_to_device

    @pushed_to_device.setter
    def pushed_to_device(self, pushed: bool) -> None:
        """setter for pushed_to_device"""
        self._pushed_to_device = pushed
        for col in self.columns:
            col._pushed_to_device = True

    def add_column(self, col: DeskColumn):
        """add a new colum"""
        self.columns.append(col)

    def remove_column(self, col: DeskColumn):
        """removes the specified column from the bank set"""
        self.columns.remove(col)

    def generate_bank_message(self) -> proto.Console_pb2.add_fader_bank_set.fader_bank:
        """This method computes a proto buf representation of the bank

        Returns:
            proto buf representation
        """
        msg = proto.Console_pb2.add_fader_bank_set.fader_bank()
        for col in self.columns:
            msg.cols.extend([col._generate_column_message()])  # TODO private Methode
        return msg

    def copy(self) -> "FaderBank":
        new_fb = FaderBank()
        for c in self.columns:
            new_fb.columns.append(c.copy())
        return new_fb


class BanksetIDUpdateListener(ABC):
    @abstractmethod
    def notify_on_new_id(self, new_id: str):
        raise NotImplementedError()


class BankSet:
    """This class represents a bank set.

    A bank set is a set of banks, the user can switch between at a given time.
    Multiple bank sets can be linked to fish at the same time but only one may be active at the same time.
    Only the GUI may specify which bank set is active any given time,
     except for the event that the active bank set will be unlinked.
    In this case fish will enable the bank set with the next lower index.
    """
    _fish_connector: "NetworkManager" = None
    _active_bank_set_id: str = None
    _active_bank_set: "BankSet" = None
    _seven_seg_data: str = "00          "
    _linked_bank_sets = []

    @classmethod
    def fish_connector(cls) -> "NetworkManager":
        """Connector of the Bank"""
        return cls._fish_connector

    @classmethod
    def linked_bank_sets(cls) -> list["BankSet"]:
        """This method yields the mutable list of bank sets that are currently loaded in fish.

        This method should only be used by friend classes.
        """
        return cls._linked_bank_sets

    @classmethod
    def active_bank_set(cls) -> "BankSet":
        """current bank set"""
        return cls._active_bank_set

    @staticmethod
    def get_linked_bank_sets() -> list["BankSet"]:
        """This method returns a copy of the linked bank sets, save to be used by non friend classes."""
        return list(BankSet._linked_bank_sets)

    def __init__(self, banks: list[FaderBank] = None, description: str = None, gui_controlled: bool = False,
                 id: str | None = None):
        """Construct a bank set object.
        After construction link() needs to be called in order to link the set with the control desk.

        Arguments:
        banks -- The initial list of fader banks
        description -- Optional. A human-readable description used in the fader bank editor to identify the set to edit
        gui_controlled -- Indicates that the set is managed by the gui thread.
        id -- If a specific ID should be used for initialization
        """
        if id:
            self._id = id
        else:
            self._id = _generate_unique_id()
        self.pushed_to_fish = False
        self._broadcaster: Broadcaster = Broadcaster()
        self.active_column: DeskColumn | None = None
        if banks:
            self.banks: list[FaderBank] = banks
        else:
            self.banks: list[FaderBank] = []
        self.active_bank = 0
        if description:
            self.description = str(description)
        else:
            self.description = "No description"
        self._gui_controlled = gui_controlled
        self._broadcaster.view_leave_colum_select.connect(self._leaf_selected)
        self.id_update_listeners: list[BanksetIDUpdateListener] = []
        # The variable below should be set to true if the topology of the bank set was changed by the GUI
        self.update_required = False

    def __del__(self):
        if self.pushed_to_fish:
            self.unlink()
        try:
            super().__del__()
        except AttributeError:
            pass

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
        self.active_bank = min(self.active_bank, bank_set_size - 1)
        old_set_id: str = self.id

        if self.is_linked:
            # new_id = _generate_unique_id()
            new_id = old_set_id
        else:
            new_id = old_set_id
        # TODO find out if we actually really need to change the ID as this messes with the filters
        BankSet._fish_connector.send_add_fader_bank_set_message(new_id, self.active_bank, self.banks)
        if self.pushed_to_fish:
            if new_id != old_set_id:
                BankSet._fish_connector.send_fader_bank_set_delete_message(old_set_id)
        else:
            BankSet._linked_bank_sets.append(self)
        if BankSet._active_bank_set_id == self.id:
            self._id = new_id
            self.activate()
        elif not BankSet._active_bank_set_id:
            self._id = new_id
            self.activate()
        else:
            self._id = new_id
        if new_id != old_set_id:
            for notifier in self.id_update_listeners:
                notifier.notify_on_new_id(new_id)
        self.pushed_to_fish = True
        if self._gui_controlled:
            self.push_messages_now()
        self.update_required = False
        return True

    @property
    def id(self) -> str:
        return self._id

    def activate(self, out_of_thread: bool = False):
        """Calling this method makes this bank set the active one.
        """
        # if BankSet._active_bank_set_id == self.id:
        #    return
        self._gui_controlled = not out_of_thread
        BankSet._active_bank_set_id = self.id
        BankSet._active_bank_set = self
        text = "Bank: " + self.description
        BankSet._seven_seg_data = (str(self.active_bank % 100) if self.active_bank > 9 else "0" + str(
            self.active_bank)) + text[-10:] + (" " * (10 - len(text)))
        self._send_desk_update_message()
        if self._gui_controlled:
            self.push_messages_now()

    def _leaf_selected(self):
        if not self.active_column:
            return
        self.active_column = None
        self._send_desk_update_message()

    def _send_desk_update_message(self):
        msg = proto.Console_pb2.desk_update()
        if self.active_column:
            msg.selected_column_id = self.active_column.id
        else:
            msg.selected_column_id = ""  # Do not update the set of selected columns yet
        msg.find_active_on_column_id = ""  # Do not update the column with active 'find fixture' feature yet
        msg.selected_bank = self.active_bank
        msg.selected_bank_set = BankSet._active_bank_set_id
        msg.seven_seg_display_data = BankSet._seven_seg_data
        BankSet._fish_connector.send_desk_update_message(msg, update_from_gui=self._gui_controlled)

    def add_bank(self, bank: FaderBank):
        """Update the fader bank on the control desk

        Warning: This operation is expensive and might interrupt the interactions of the user. Add all columns to the
        bank at first. If all you'd like to do is updating a column: call the update function on that column.
        """
        self.banks.append(bank)  # TODO ein BankSet has no columns attribute
        for col in bank.columns:
            col.bank_set = self
        self.update()

    def add_column_to_next_bank(self, f: DeskColumn):
        """This method adds the provided column f to the last not full bank set."""
        if len(self.banks) == 0:
            self.add_bank(FaderBank())
        if len(self.banks[-1].columns) >= 8:  # TODO query actual bank width
            self.add_bank(FaderBank())
        self.banks[-1].add_column(f)
        f.bank_set = self

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
        found_index = -1
        for linked_bank in BankSet._linked_bank_sets:
            if linked_bank.id == self.id:
                found_index = i
                break

            i += 1
        if found_index != -1:
            BankSet._fish_connector.send_fader_bank_set_delete_message(self.id)
            BankSet._linked_bank_sets.pop(found_index)
        self.pushed_to_fish = False
        return True

    @property
    def is_linked(self) -> bool:
        """Returns True if the bank set is loaded to fish."""
        return self.pushed_to_fish

    @property
    def is_empty(self) -> bool:
        """Returns true if the bank set is empty."""
        return len(self.banks) == 0

    @staticmethod
    def push_messages_now():
        """This method pushes outstanding updates to fish. It should only be called within the Qt event loop."""
        BankSet._fish_connector.push_messages()

    def get_column(self, column_id: str) -> DeskColumn | None:
        """This method returns the column requested by the provided id or None if it could not be found.

        :param column_id: The id of the column to search for
        :returns: The column or None.
        """
        for b in self.banks:
            for c in b.columns:
                if c.id == column_id:
                    return c
        return None

    def set_active_column(self, column: DeskColumn):
        self.active_column = column

    def get_column_by_number(self, index: int) -> DeskColumn:
        """This method iterates through the banks and returns column i"""
        i = 0
        # Unfortunately we cannot return the index directly, as the number of columns in a bank is not constant.
        for b in self.banks:
            for c in b.columns:
                if i == index:
                    return c

                i += 1

    @staticmethod
    def handle_column_update_message(message: proto.Console_pb2.fader_column):
        col = BankSet._active_bank_set.get_column(message.column_id)
        if col:
            col.update_from_message(message)

    def copy(self) -> "BankSet":
        new_bs = BankSet(description=self.description, gui_controlled=self._gui_controlled)
        for b in self.banks:
            new_bs.banks.append(b.copy())
        return new_bs


def set_network_manager(network_manager: "NetworkManager"):
    """Set the network manager instance to be used by all bank sets and subsequent banks and columns."""
    BankSet._fish_connector = network_manager


def set_seven_seg_display_content(content: str, update_from_gui: bool = False):
    """Set the content of the 7seg displays of connected X-Touch controllers.

    Fish will truncate any text longer than 12 chars and
    only guarantees the correct display of hexadecimal characters due to the limitations of seven segment displays.
    """
    BankSet._seven_seg_data = content[0:12] + " " * (12 - len(content))
    send_independent_update_msg(update_from_gui)


def send_independent_update_msg(update_from_gui: bool):
    bs = BankSet.active_bank_set()
    if not bs:
        return
    abs_id = bs.id
    if abs_id:
        for bs in BankSet.linked_bank_sets():
            if bs.id == abs_id:
                bs._send_desk_update_message()
                return
    msg = proto.Console_pb2.desk_update()
    msg.selected_column_id = ""  # Do not update the set of selected columns yet
    msg.find_active_on_column_id = ""  # Do not update the column with active 'find fixture' feature yet
    msg.selected_bank = 0
    msg.selected_bank_set = ""
    msg.seven_seg_display_data = BankSet._seven_seg_data
    BankSet._fish_connector.send_desk_update_message(msg, update_from_gui)


def commit_all_bank_sets():
    """This method calls update on all linked columns.

    This is useful in the event of a reconnect to fish as the state of fish is unknown at this point in time.
    """
    bank_set_for_activation = None
    for bs in BankSet.linked_bank_sets():
        bs.update()
        if bs.id == BankSet.active_bank_set().id:
            bank_set_for_activation = bs
    if bank_set_for_activation:
        bank_set_for_activation.activate()
