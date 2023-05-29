# coding=utf-8
"""All messages send to the x-touch"""

import proto.Console_pb2
import proto.MessageTypes_pb2
from model.broadcaster import Broadcaster

VIEW_PATCH_MENU_MSG: proto.Console_pb2.button_state_change = proto.Console_pb2.button_state_change(
    button=proto.Console_pb2.ButtonCode.BTN_PLUGIN_PATCH, new_state=proto.Console_pb2.ButtonState.BS_ACTIVE)

VIEW_NOT_PATCH_MENU_MSG: proto.Console_pb2.button_state_change = proto.Console_pb2.button_state_change(
    button=proto.Console_pb2.ButtonCode.BTN_PLUGIN_PATCH, new_state=proto.Console_pb2.ButtonState.BS_SET_LED_NOT_ACTIVE)

VIEW_PATCHING_MSG: proto.Console_pb2.button_state_change = proto.Console_pb2.button_state_change(
    button=proto.Console_pb2.ButtonCode.BTN_PLUGIN_PATCH, new_state=proto.Console_pb2.ButtonState.BS_SET_LED_BLINKING)

VIEW_FILTER_MENU_MSG: proto.Console_pb2.button_state_change = proto.Console_pb2.button_state_change(
    button=proto.Console_pb2.ButtonCode.BTN_TRACK_EDITSHOW, new_state=proto.Console_pb2.ButtonState.BS_ACTIVE)

VIEW_NOT_FILTER_MENU_MSG: proto.Console_pb2.button_state_change = proto.Console_pb2.button_state_change(
    button=proto.Console_pb2.ButtonCode.BTN_TRACK_EDITSHOW,
    new_state=proto.Console_pb2.ButtonState.BS_SET_LED_NOT_ACTIVE)

VIEW_COLOR_MSG: proto.Console_pb2.button_state_change = proto.Console_pb2.button_state_change(
    button=proto.Console_pb2.ButtonCode.BTN_DROP_COLOR, new_state=proto.Console_pb2.ButtonState.BS_ACTIVE)

VIEW_NOT_COLOR_MSG: proto.Console_pb2.button_state_change = proto.Console_pb2.button_state_change(
    button=proto.Console_pb2.ButtonCode.BTN_DROP_COLOR, new_state=proto.Console_pb2.ButtonState.BS_SET_LED_NOT_ACTIVE)

VIEW_TEMPERATURE_MSG: proto.Console_pb2.button_state_change = proto.Console_pb2.button_state_change(
    button=proto.Console_pb2.ButtonCode.BTN_REPLACE_TEMPERATURE, new_state=proto.Console_pb2.ButtonState.BS_ACTIVE)

VIEW_NOT_TEMPERATURE_MSG: proto.Console_pb2.button_state_change = proto.Console_pb2.button_state_change(
    button=proto.Console_pb2.ButtonCode.BTN_REPLACE_TEMPERATURE,
    new_state=proto.Console_pb2.ButtonState.BS_SET_LED_NOT_ACTIVE)


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

        self._broadcaster.view_to_color.connect(lambda: send(VIEW_COLOR_MSG))
        self._broadcaster.view_leave_color.connect(lambda: send(VIEW_NOT_COLOR_MSG))

        self._broadcaster.view_to_temperature.connect(lambda: send(VIEW_TEMPERATURE_MSG))
        self._broadcaster.view_leave_temperature.connect(lambda: send(VIEW_NOT_TEMPERATURE_MSG))
