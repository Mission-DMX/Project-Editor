# coding=utf-8
"""All messages send to the x-touch"""

import proto.Console_pb2
import proto.MessageTypes_pb2
from model.broadcaster import Broadcaster

VIEW_PATCH_MENU_MSG: proto.MessageTypes_pb2 = proto.Console_pb2.button_state_change(
    button=proto.Console_pb2.ButtonCode.BTN_PLUGIN_PATCH, new_state=proto.Console_pb2.ButtonState.BS_ACTIVE)

VIEW_NOT_PATCH_MENU_MSG: proto.MessageTypes_pb2 = proto.Console_pb2.button_state_change(
    button=proto.Console_pb2.ButtonCode.BTN_PLUGIN_PATCH, new_state=proto.Console_pb2.ButtonState.BS_SET_LED_NOT_ACTIVE)

VIEW_PATCHING_MSG: proto.MessageTypes_pb2 = proto.Console_pb2.button_state_change(
    button=proto.Console_pb2.ButtonCode.BTN_PLUGIN_PATCH, new_state=proto.Console_pb2.ButtonState.BS_SET_LED_BLINKING)

VIEW_FILTER_MENU_MSG: proto.MessageTypes_pb2 = proto.Console_pb2.button_state_change(
    button=proto.Console_pb2.ButtonCode.BTN_TRACK_EDITSHOW, new_state=proto.Console_pb2.ButtonState.BS_ACTIVE)

VIEW_NOT_FILTER_MENU_MSG: proto.MessageTypes_pb2 = proto.Console_pb2.button_state_change(
    button=proto.Console_pb2.ButtonCode.BTN_TRACK_EDITSHOW,
    new_state=proto.Console_pb2.ButtonState.BS_SET_LED_NOT_ACTIVE)


class XTochMessages():
    def __init__(self, broadcaster: Broadcaster, send: callable) -> None:
        self._broadcaster = broadcaster

        # listen on updates
        self._broadcaster.view_to_patch_menu.connect(lambda: send(VIEW_PATCH_MENU_MSG))
        self._broadcaster.view_leave_patch_menu.connect(lambda: send(VIEW_NOT_PATCH_MENU_MSG))

        self._broadcaster.view_patching.connect(lambda: send(VIEW_PATCHING_MSG))
        self._broadcaster.view_leave_patching.connect(lambda: send(VIEW_PATCH_MENU_MSG))

        self._broadcaster.view_to_file_editor.connect(lambda: send(VIEW_FILTER_MENU_MSG))
        self._broadcaster.view_leave_file_editor.connect(lambda: send(VIEW_NOT_FILTER_MENU_MSG))