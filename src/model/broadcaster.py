"""connector for Signals"""
from __future__ import annotations

from typing import Any
from xml.etree.ElementTree import Element

from PySide6 import QtCore

import proto.DirectMode_pb2
import proto.Events_pb2
import proto.FilterMode_pb2
import proto.RealTimeControl_pb2
from controller.joystick.joystick_enum import JoystickList

from .device import Device
from .scene import FilterPage, Scene


class QObjectSingletonMeta(type(QtCore.QObject)):
    """metaclass for a QObject Singleton"""
    instance: Any

    def __init__(cls: type[QObjectSingletonMeta], name: str, bases: tuple[type, ...], _dict: dict[str, Any]) -> None:
        super().__init__(name, bases, _dict)
        cls.instance = None

    def __call__(cls: type[QObjectSingletonMeta], *args: Any, **kw: Any) -> QtCore.QObject:
        if cls.instance is None:
            cls.instance = super().__call__(*args, **kw)
        return cls.instance


class Broadcaster(QtCore.QObject, metaclass=QObjectSingletonMeta):
    """connector for Signals"""

    connection_state_updated: QtCore.Signal = QtCore.Signal(bool)
    change_run_mode: QtCore.Signal = QtCore.Signal(proto.RealTimeControl_pb2.RunMode.ValueType)  # TODO Remove
    change_active_scene: QtCore.Signal = QtCore.Signal(Scene)
    load_show_file: QtCore.Signal = QtCore.Signal(Element, bool)
    show_file_loaded: QtCore.Signal = QtCore.Signal()
    show_file_path_changed: QtCore.Signal = QtCore.Signal(str)
    add_universe: QtCore.Signal = QtCore.Signal(object)
    add_fixture: QtCore.Signal = QtCore.Signal(object)
    send_universe: QtCore.Signal = QtCore.Signal(object)
    send_universe_value: QtCore.Signal = QtCore.Signal(object)
    send_request_dmx_data: QtCore.Signal = QtCore.Signal(object)
    request_main_brightness_fader_update: QtCore.Signal = QtCore.Signal(int)
    ################################################################
    clear_board_configuration: QtCore.Signal = QtCore.Signal()
    board_configuration_loaded: QtCore.Signal = QtCore.Signal(str)
    scene_created: QtCore.Signal = QtCore.Signal(Scene)
    scene_open_in_editor_requested: QtCore.Signal = QtCore.Signal(FilterPage)
    bankset_open_in_editor_requested: QtCore.Signal = QtCore.Signal(dict)
    uipage_opened_in_editor_requested: QtCore.Signal = QtCore.Signal(dict)
    delete_scene: QtCore.Signal = QtCore.Signal(Scene)
    delete_universe: QtCore.Signal = QtCore.Signal(object)
    device_created: QtCore.Signal = QtCore.Signal(Device)
    delete_device: QtCore.Signal = QtCore.Signal(Device)
    event_sender_model_updated: QtCore.Signal = QtCore.Signal()
    fish_event_received: QtCore.Signal = QtCore.Signal(proto.Events_pb2.event)
    event_rename_action_occurred: QtCore.Signal = QtCore.Signal(int)  # int: the id of the sender where the rename was
    uipage_renamed: QtCore.Signal = QtCore.Signal(int)  # The ID of the parent scene
    macro_added_to_show_file: QtCore.Signal = QtCore.Signal(int)  # int: The index of the new macro in the board config
    ################################################################
    view_to_patch_menu: QtCore.Signal = QtCore.Signal()
    view_patching: QtCore.Signal = QtCore.Signal()
    view_leave_patching: QtCore.Signal = QtCore.Signal()
    view_leave_patch_menu: QtCore.Signal = QtCore.Signal()

    view_to_show_player: QtCore.Signal = QtCore.Signal()
    view_leave_show_player: QtCore.Signal = QtCore.Signal()

    view_to_file_editor: QtCore.Signal = QtCore.Signal()
    view_leave_file_editor: QtCore.Signal = QtCore.Signal()

    view_leave_colum_select: QtCore.Signal = QtCore.Signal()
    view_change_colum_select: QtCore.Signal = QtCore.Signal()

    view_to_color: QtCore.Signal = QtCore.Signal()
    view_leave_color: QtCore.Signal = QtCore.Signal()

    view_to_temperature: QtCore.Signal = QtCore.Signal()
    view_leave_temperature: QtCore.Signal = QtCore.Signal()

    view_to_console_mode: QtCore.Signal = QtCore.Signal()
    view_leave_console_mode: QtCore.Signal = QtCore.Signal()

    view_to_action_config: QtCore.Signal = QtCore.Signal()
    view_leave_action_config: QtCore.Signal = QtCore.Signal()
    application_closing: QtCore.Signal = QtCore.Signal()
    ################################################################
    save_button_pressed: QtCore.Signal = QtCore.Signal()
    commit_button_pressed: QtCore.Signal = QtCore.Signal()
    jogwheel_rotated_left: QtCore.Signal = QtCore.Signal()
    jogwheel_rotated_right: QtCore.Signal = QtCore.Signal()
    desk_media_rev_pressed: QtCore.Signal = QtCore.Signal()
    desk_media_forward_pressed: QtCore.Signal = QtCore.Signal()
    desk_media_stop_pressed: QtCore.Signal = QtCore.Signal()
    desk_media_play_pressed: QtCore.Signal = QtCore.Signal()
    desk_media_rec_pressed: QtCore.Signal = QtCore.Signal()
    desk_media_scrub_pressed: QtCore.Signal = QtCore.Signal()
    desk_media_scrub_released: QtCore.Signal = QtCore.Signal()
    desk_f_key_pressed: QtCore.Signal = QtCore.Signal(int)

    handle_joystick_event: QtCore.Signal = QtCore.Signal(JoystickList, float, bool)
    joystick_selected_event: QtCore.Signal = QtCore.Signal(JoystickList)
    #################################################################
    update_filter_parameter: QtCore.Signal = QtCore.Signal(proto.FilterMode_pb2.update_parameter)
    active_scene_switched: QtCore.Signal = QtCore.Signal(int)
    #################################################################
    select_column_id: QtCore.Signal = QtCore.Signal(str)
    log_message: QtCore.Signal = QtCore.Signal(str)
    dmx_from_fish: QtCore.Signal = QtCore.Signal(proto.DirectMode_pb2.dmx_output)

    def __new__(cls, *args, **kwargs) -> Broadcaster:
        if not hasattr(cls, "instance") or cls.instance is None:
            cls.instance = super().__new__(cls)
        return cls.instance
