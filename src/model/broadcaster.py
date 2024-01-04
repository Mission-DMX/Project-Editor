# coding=utf-8
"""connector for Signals"""
from xml.etree.ElementTree import Element

from PySide6 import QtCore

from proto.RealTimeControl_pb2 import RunMode
from proto.FilterMode_pb2 import update_parameter

from model.patching_universe import PatchingUniverse
from view.dialogs.patching_dialog import PatchingDialog

from .device import Device
from .scene import Scene, FilterPage
from .universe import Universe


class QObjectSingletonMeta(type(QtCore.QObject)):
    """metaclass for a QObject Singleton"""

    def __init__(cls, name, bases, _dict):
        super().__init__(name, bases, _dict)
        cls.instance = None

    def __call__(cls, *args, **kw):
        if cls.instance is None:
            cls.instance = super().__call__(*args, **kw)
        return cls.instance


class Broadcaster(QtCore.QObject, metaclass=QObjectSingletonMeta):
    """connector for Signals"""
    connection_state_updated: QtCore.Signal = QtCore.Signal(bool)
    change_run_mode: QtCore.Signal = QtCore.Signal(RunMode.ValueType) # TODO Remove
    change_active_scene: QtCore.Signal = QtCore.Signal(Scene)
    load_show_file: QtCore.Signal = QtCore.Signal(Element, bool)
    show_file_loaded: QtCore.Signal = QtCore.Signal()
    show_file_path_changed: QtCore.Signal = QtCore.Signal(str)
    add_universe: QtCore.Signal = QtCore.Signal(PatchingUniverse)
    send_universe: QtCore.Signal = QtCore.Signal(PatchingUniverse)
    send_universe_value: QtCore.Signal = QtCore.Signal(Universe)
    ################################################################
    clear_board_configuration: QtCore.Signal = QtCore.Signal()
    board_configuration_loaded: QtCore.Signal = QtCore.Signal(str)
    scene_created: QtCore.Signal = QtCore.Signal(Scene)
    scene_open_in_editor_requested: QtCore.Signal = QtCore.Signal(FilterPage)
    bankset_open_in_editor_requested: QtCore.Signal = QtCore.Signal(dict)
    uipage_opened_in_editor_requested: QtCore.Signal = QtCore.Signal(dict)
    delete_scene: QtCore.Signal = QtCore.Signal(Scene)
    delete_universe: QtCore.Signal = QtCore.Signal(Universe)
    device_created: QtCore.Signal = QtCore.Signal(Device)
    delete_device: QtCore.Signal = QtCore.Signal(Device)
    fixture_patched: QtCore.Signal = QtCore.Signal()
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
    #################################################################
    update_filter_parameter: QtCore.Signal = QtCore.Signal(update_parameter)
    #################################################################
    select_column_id: QtCore.Signal = QtCore.Signal(str)
    patching_universes: list[PatchingUniverse] = []

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "instance") or cls.instance is None:
            cls.instance = super(Broadcaster, cls).__new__(cls)
        return cls.instance
