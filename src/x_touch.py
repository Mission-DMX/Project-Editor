"""All messages send to the x-touch"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QApplication

import proto.Console_pb2
import proto.MessageTypes_pb2
from model.control_desk import set_seven_seg_display_content

if TYPE_CHECKING:
    from model.broadcaster import Broadcaster

VIEW_PATCH_MENU_MSG: proto.Console_pb2.button_state_change = proto.Console_pb2.button_state_change(
    button=proto.Console_pb2.ButtonCode.BTN_PLUGIN_PATCH, new_state=proto.Console_pb2.ButtonState.BS_ACTIVE
)

VIEW_NOT_PATCH_MENU_MSG: proto.Console_pb2.button_state_change = proto.Console_pb2.button_state_change(
    button=proto.Console_pb2.ButtonCode.BTN_PLUGIN_PATCH, new_state=proto.Console_pb2.ButtonState.BS_SET_LED_NOT_ACTIVE
)

VIEW_PATCHING_MSG: proto.Console_pb2.button_state_change = proto.Console_pb2.button_state_change(
    button=proto.Console_pb2.ButtonCode.BTN_PLUGIN_PATCH, new_state=proto.Console_pb2.ButtonState.BS_SET_LED_BLINKING
)

VIEW_FILTER_MENU_MSG: proto.Console_pb2.button_state_change = proto.Console_pb2.button_state_change(
    button=proto.Console_pb2.ButtonCode.BTN_PAN_EDITSHOW, new_state=proto.Console_pb2.ButtonState.BS_ACTIVE
)

VIEW_NOT_FILTER_MENU_MSG: proto.Console_pb2.button_state_change = proto.Console_pb2.button_state_change(
    button=proto.Console_pb2.ButtonCode.BTN_PAN_EDITSHOW, new_state=proto.Console_pb2.ButtonState.BS_SET_LED_NOT_ACTIVE
)

VIEW_SHOW_MENU_MSG: proto.Console_pb2.button_state_change = proto.Console_pb2.button_state_change(
    button=proto.Console_pb2.ButtonCode.BTN_EQ_SHOWUI, new_state=proto.Console_pb2.ButtonState.BS_ACTIVE
)

VIEW_NOT_SHOW_MENU: proto.Console_pb2.button_state_change = proto.Console_pb2.button_state_change(
    button=proto.Console_pb2.ButtonCode.BTN_EQ_SHOWUI, new_state=proto.Console_pb2.ButtonState.BS_SET_LED_NOT_ACTIVE
)

VIEW_CONSOLE_MODE: proto.Console_pb2.button_state_change = proto.Console_pb2.button_state_change(
    button=proto.Console_pb2.ButtonCode.BTN_TRACK_CONSOLE, new_state=proto.Console_pb2.ButtonState.BS_ACTIVE
)

VIEW_NOT_CONSOLSE_MODE: proto.Console_pb2.button_state_change = proto.Console_pb2.button_state_change(
    button=proto.Console_pb2.ButtonCode.BTN_TRACK_CONSOLE, new_state=proto.Console_pb2.ButtonState.BS_SET_LED_NOT_ACTIVE
)

VIEW_COLOR_MSG: proto.Console_pb2.button_state_change = proto.Console_pb2.button_state_change(
    button=proto.Console_pb2.ButtonCode.BTN_DROP_COLOR, new_state=proto.Console_pb2.ButtonState.BS_ACTIVE
)

VIEW_NOT_COLOR_MSG: proto.Console_pb2.button_state_change = proto.Console_pb2.button_state_change(
    button=proto.Console_pb2.ButtonCode.BTN_DROP_COLOR, new_state=proto.Console_pb2.ButtonState.BS_SET_LED_NOT_ACTIVE
)

VIEW_TEMPERATURE_MSG: proto.Console_pb2.button_state_change = proto.Console_pb2.button_state_change(
    button=proto.Console_pb2.ButtonCode.BTN_REPLACE_TEMPERATURE, new_state=proto.Console_pb2.ButtonState.BS_ACTIVE
)

VIEW_NOT_TEMPERATURE_MSG: proto.Console_pb2.button_state_change = proto.Console_pb2.button_state_change(
    button=proto.Console_pb2.ButtonCode.BTN_REPLACE_TEMPERATURE,
    new_state=proto.Console_pb2.ButtonState.BS_SET_LED_NOT_ACTIVE,
)

SAVE_BUTTON_ACTIVE_MSG: proto.Console_pb2.button_state_change = proto.Console_pb2.button_state_change(
    button=proto.Console_pb2.ButtonCode.BTN_SAVE_SAVE,
    new_state=proto.Console_pb2.ButtonState.BS_ACTIVE,
)

SAVE_BUTTON_DEACTIVATE_MSG: proto.Console_pb2.button_state_change = proto.Console_pb2.button_state_change(
    button=proto.Console_pb2.ButtonCode.BTN_SAVE_SAVE,
    new_state=proto.Console_pb2.ButtonState.BS_SET_LED_NOT_ACTIVE,
)


class XTouchMessages:
    """messages to the XTouch"""

    def __init__(self, broadcaster: Broadcaster, send: callable) -> None:
        self._broadcaster = broadcaster

        # listen on updates
        self._broadcaster.view_to_patch_menu.connect(lambda: send(VIEW_PATCH_MENU_MSG))
        self._broadcaster.view_leave_patch_menu.connect(lambda: send(VIEW_NOT_PATCH_MENU_MSG))

        self._broadcaster.view_patching.connect(lambda: send(VIEW_PATCHING_MSG))
        self._broadcaster.view_leave_patching.connect(lambda: send(VIEW_PATCH_MENU_MSG))

        self._broadcaster.view_to_file_editor.connect(lambda: send(VIEW_FILTER_MENU_MSG))
        self._broadcaster.view_leave_file_editor.connect(lambda: send(VIEW_NOT_FILTER_MENU_MSG))

        self._broadcaster.view_to_show_player.connect(lambda: send(VIEW_SHOW_MENU_MSG))
        self._broadcaster.view_leave_show_player.connect(lambda: send(VIEW_NOT_SHOW_MENU))

        self._broadcaster.view_to_console_mode.connect(lambda: send(VIEW_CONSOLE_MODE))
        self._broadcaster.view_leave_console_mode.connect(lambda: send(VIEW_NOT_CONSOLSE_MODE))

        self._broadcaster.view_to_color.connect(lambda: send(VIEW_COLOR_MSG))
        self._broadcaster.view_leave_color.connect(lambda: send(VIEW_NOT_COLOR_MSG))

        self._broadcaster.view_to_temperature.connect(lambda: send(VIEW_TEMPERATURE_MSG))
        self._broadcaster.view_leave_temperature.connect(lambda: send(VIEW_NOT_TEMPERATURE_MSG))
        self._broadcaster.show_file_path_changed.connect(self._update_save_button)
        self._broadcaster.application_closing.connect(self._cleanup_xtouch)
        self._send: callable = send

    def _update_save_button(self, file_path: str) -> None:
        if file_path:
            self._send(SAVE_BUTTON_ACTIVE_MSG)
        else:
            self._send(SAVE_BUTTON_DEACTIVATE_MSG)

    def _cleanup_xtouch(self) -> None:
        self._send(VIEW_NOT_PATCH_MENU_MSG)
        self._send(VIEW_NOT_FILTER_MENU_MSG)
        self._send(VIEW_NOT_PATCH_MENU_MSG)
        self._send(VIEW_NOT_SHOW_MENU)
        self._send(VIEW_NOT_CONSOLSE_MODE)
        self._send(VIEW_NOT_COLOR_MSG)
        self._send(VIEW_NOT_TEMPERATURE_MSG)
        self._send(SAVE_BUTTON_DEACTIVATE_MSG)
        set_seven_seg_display_content(" " * 12, update_from_gui=True)
        QApplication.processEvents()
