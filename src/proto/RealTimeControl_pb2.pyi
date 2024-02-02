import UniverseControl_pb2 as _UniverseControl_pb2
import DirectMode_pb2 as _DirectMode_pb2
import FilterMode_pb2 as _FilterMode_pb2
import Console_pb2 as _Console_pb2
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union
from UniverseControl_pb2 import Universe as Universe
from UniverseControl_pb2 import universes_list as universes_list
from UniverseControl_pb2 import request_universe_list as request_universe_list
from UniverseControl_pb2 import delete_universe as delete_universe
from DirectMode_pb2 import dmx_output as dmx_output
from DirectMode_pb2 import request_dmx_data as request_dmx_data
from FilterMode_pb2 import enter_scene as enter_scene
from FilterMode_pb2 import load_show_file as load_show_file
from FilterMode_pb2 import update_parameter as update_parameter
from FilterMode_pb2 import ShowFileApplyState as ShowFileApplyState
from Console_pb2 import button_state_change as button_state_change
from Console_pb2 import fader_position as fader_position
from Console_pb2 import rotary_encoder_change as rotary_encoder_change
from Console_pb2 import remove_fader_bank_set as remove_fader_bank_set
from Console_pb2 import desk_update as desk_update
from Console_pb2 import fader_column as fader_column
from Console_pb2 import add_fader_bank_set as add_fader_bank_set
from Console_pb2 import ButtonState as ButtonState
from Console_pb2 import ButtonCode as ButtonCode
from Console_pb2 import lcd_color as lcd_color

DESCRIPTOR: _descriptor.FileDescriptor
SFAS_INVALID: _FilterMode_pb2.ShowFileApplyState
SFAS_SHOW_ACTIVE: _FilterMode_pb2.ShowFileApplyState
SFAS_SHOW_LOADING: _FilterMode_pb2.ShowFileApplyState
SFAS_SHOW_UPDATING: _FilterMode_pb2.ShowFileApplyState
SFAS_NO_SHOW_ERROR: _FilterMode_pb2.ShowFileApplyState
SFAS_ERROR_SHOW_RUNNING: _FilterMode_pb2.ShowFileApplyState
BS_SET_LED_NOT_ACTIVE: _Console_pb2.ButtonState
BS_ACTIVE: _Console_pb2.ButtonState
BS_SET_LED_BLINKING: _Console_pb2.ButtonState
BS_BUTTON_PRESSED: _Console_pb2.ButtonState
BS_BUTTON_RELEASED: _Console_pb2.ButtonState
BTN_CH1_ENCODER_ROTARYMODE: _Console_pb2.ButtonCode
BTN_CH2_ENCODER_ROTARYMODE: _Console_pb2.ButtonCode
BTN_CH3_ENCODER_ROTARYMODE: _Console_pb2.ButtonCode
BTN_CH4_ENCODER_ROTARYMODE: _Console_pb2.ButtonCode
BTN_CH5_ENCODER_ROTARYMODE: _Console_pb2.ButtonCode
BTN_CH6_ENCODER_ROTARYMODE: _Console_pb2.ButtonCode
BTN_CH7_ENCODER_ROTARYMODE: _Console_pb2.ButtonCode
BTN_CH8_ENCODER_ROTARYMODE: _Console_pb2.ButtonCode
BTN_CH1_REC_READY: _Console_pb2.ButtonCode
BTN_CH2_REC_READY: _Console_pb2.ButtonCode
BTN_CH3_REC_READY: _Console_pb2.ButtonCode
BTN_CH4_REC_READY: _Console_pb2.ButtonCode
BTN_CH5_REC_READY: _Console_pb2.ButtonCode
BTN_CH6_REC_READY: _Console_pb2.ButtonCode
BTN_CH7_REC_READY: _Console_pb2.ButtonCode
BTN_CH8_REC_READY: _Console_pb2.ButtonCode
BTN_CH1_SOLO_FLASH: _Console_pb2.ButtonCode
BTN_CH2_SOLO_FLASH: _Console_pb2.ButtonCode
BTN_CH3_SOLO_FLASH: _Console_pb2.ButtonCode
BTN_CH4_SOLO_FLASH: _Console_pb2.ButtonCode
BTN_CH5_SOLO_FLASH: _Console_pb2.ButtonCode
BTN_CH6_SOLO_FLASH: _Console_pb2.ButtonCode
BTN_CH7_SOLO_FLASH: _Console_pb2.ButtonCode
BTN_CH8_SOLO_FLASH: _Console_pb2.ButtonCode
BTN_CH1_MUTE_BLACK: _Console_pb2.ButtonCode
BTN_CH2_MUTE_BLACK: _Console_pb2.ButtonCode
BTN_CH3_MUTE_BLACK: _Console_pb2.ButtonCode
BTN_CH4_MUTE_BLACK: _Console_pb2.ButtonCode
BTN_CH5_MUTE_BLACK: _Console_pb2.ButtonCode
BTN_CH6_MUTE_BLACK: _Console_pb2.ButtonCode
BTN_CH7_MUTE_BLACK: _Console_pb2.ButtonCode
BTN_CH8_MUTE_BLACK: _Console_pb2.ButtonCode
BTN_CH1_SELECT_SELECT: _Console_pb2.ButtonCode
BTN_CH2_SELECT_SELECT: _Console_pb2.ButtonCode
BTN_CH3_SELECT_SELECT: _Console_pb2.ButtonCode
BTN_CH4_SELECT_SELECT: _Console_pb2.ButtonCode
BTN_CH5_SELECT_SELECT: _Console_pb2.ButtonCode
BTN_CH6_SELECT_SELECT: _Console_pb2.ButtonCode
BTN_CH7_SELECT_SELECT: _Console_pb2.ButtonCode
BTN_CH8_SELECT_SELECT: _Console_pb2.ButtonCode
BTN_TRACK_CONSOLE: _Console_pb2.ButtonCode
BTN_PAN_EDITSHOW: _Console_pb2.ButtonCode
BTN_EQ_SHOWUI: _Console_pb2.ButtonCode
BTN_SEND_VISUALIZER: _Console_pb2.ButtonCode
BTN_PLUGIN_PATCH: _Console_pb2.ButtonCode
BTN_INST_DEBUG: _Console_pb2.ButtonCode
BTN_NAMEVALUE_COMMITSHOW: _Console_pb2.ButtonCode
BTN_BEATS_OOPS: _Console_pb2.ButtonCode
BTN_GLOBALVIEW_COMMITRDY: _Console_pb2.ButtonCode
BTN_MIDITRACKS_FIND: _Console_pb2.ButtonCode
BTN_INPUTS_EVENTS: _Console_pb2.ButtonCode
BTN_AUDIOTRACKS: _Console_pb2.ButtonCode
BTN_AUDIOINST: _Console_pb2.ButtonCode
BTN_AUX: _Console_pb2.ButtonCode
BTN_BUSSES: _Console_pb2.ButtonCode
BTN_OUTPUTS: _Console_pb2.ButtonCode
BTN_USER: _Console_pb2.ButtonCode
BTN_FLIP_MAINDARK: _Console_pb2.ButtonCode
BTN_F1_F1: _Console_pb2.ButtonCode
BTN_F2_F2: _Console_pb2.ButtonCode
BTN_F3_F3: _Console_pb2.ButtonCode
BTN_F4_F4: _Console_pb2.ButtonCode
BTN_F5_F5: _Console_pb2.ButtonCode
BTN_F6_F6: _Console_pb2.ButtonCode
BTN_F7_F7: _Console_pb2.ButtonCode
BTN_F8_F8: _Console_pb2.ButtonCode
BTN_SHIFT: _Console_pb2.ButtonCode
BTN_OPTION: _Console_pb2.ButtonCode
BTN_CONTROL: _Console_pb2.ButtonCode
BTN_ALT: _Console_pb2.ButtonCode
BTN_READOFF_GOTO: _Console_pb2.ButtonCode
BTN_WRITE_MOVEWINDOW: _Console_pb2.ButtonCode
BTN_TOUCH: _Console_pb2.ButtonCode
BTN_LATCH: _Console_pb2.ButtonCode
BTN_TRIM: _Console_pb2.ButtonCode
BTN_GROUP: _Console_pb2.ButtonCode
BTN_SAVE_SAVE: _Console_pb2.ButtonCode
BTN_UNDO_UNDO: _Console_pb2.ButtonCode
BTN_CANCEL_CANCEL: _Console_pb2.ButtonCode
BTN_ENTER_ENTER: _Console_pb2.ButtonCode
BTN_MARKER_GOBO: _Console_pb2.ButtonCode
BTN_NUDGE_STROBO: _Console_pb2.ButtonCode
BTN_CYCLE_SHUTTER: _Console_pb2.ButtonCode
BTN_DROP_COLOR: _Console_pb2.ButtonCode
BTN_REPLACE_TEMPERATURE: _Console_pb2.ButtonCode
BTN_CLICK_IMAGE: _Console_pb2.ButtonCode
BTN_SOLO_SPEED: _Console_pb2.ButtonCode
BTN_REV_LASTCUE: _Console_pb2.ButtonCode
BTN_FF_NEXTCUE: _Console_pb2.ButtonCode
BTN_STOP_STOPCUE: _Console_pb2.ButtonCode
BTN_PLAY_RUNCUE: _Console_pb2.ButtonCode
BTN_REC_RECFRAME: _Console_pb2.ButtonCode
BTN_FADERBANKPREV_FADERBANKPREV: _Console_pb2.ButtonCode
BTN_FADERBANKNEXT_FADERBANKNEXT: _Console_pb2.ButtonCode
BTN_CHPREV_UNIVERSEPREV: _Console_pb2.ButtonCode
BTN_CHNEXT_UNIVERSENEXT: _Console_pb2.ButtonCode
BTN_SCRUB_JOGWHEELMODESWITCH: _Console_pb2.ButtonCode
BTN_CROSSENTER: _Console_pb2.ButtonCode
BTN_UP_UP: _Console_pb2.ButtonCode
BTN_DOWN_DOWN: _Console_pb2.ButtonCode
BTN_RIGHT_RIGHT: _Console_pb2.ButtonCode
BTN_LEFT_LEFT: _Console_pb2.ButtonCode
FADERTOUCH_CH1: _Console_pb2.ButtonCode
FADERTOUCH_CH2: _Console_pb2.ButtonCode
FADERTOUCH_CH3: _Console_pb2.ButtonCode
FADERTOUCH_CH4: _Console_pb2.ButtonCode
FADERTOUCH_CH5: _Console_pb2.ButtonCode
FADERTOUCH_CH6: _Console_pb2.ButtonCode
FADERTOUCH_CH7: _Console_pb2.ButtonCode
FADERTOUCH_CH8: _Console_pb2.ButtonCode
FADERTOUCH_MAIN: _Console_pb2.ButtonCode
black: _Console_pb2.lcd_color
red: _Console_pb2.lcd_color
green: _Console_pb2.lcd_color
yellow: _Console_pb2.lcd_color
blue: _Console_pb2.lcd_color
magenta: _Console_pb2.lcd_color
cyan: _Console_pb2.lcd_color
white: _Console_pb2.lcd_color

class RunMode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    RM_FILTER: _ClassVar[RunMode]
    RM_DIRECT: _ClassVar[RunMode]
    RM_STOP: _ClassVar[RunMode]

class LogLevel(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    LL_DEBUG: _ClassVar[LogLevel]
    LL_INFO: _ClassVar[LogLevel]
    LL_WARNING: _ClassVar[LogLevel]
    LL_ERROR: _ClassVar[LogLevel]
RM_FILTER: RunMode
RM_DIRECT: RunMode
RM_STOP: RunMode
LL_DEBUG: LogLevel
LL_INFO: LogLevel
LL_WARNING: LogLevel
LL_ERROR: LogLevel

class update_state(_message.Message):
    __slots__ = ("new_state",)
    NEW_STATE_FIELD_NUMBER: _ClassVar[int]
    new_state: RunMode
    def __init__(self, new_state: _Optional[_Union[RunMode, str]] = ...) -> None: ...

class current_state_update(_message.Message):
    __slots__ = ("current_state", "showfile_apply_state", "current_scene", "last_cycle_time", "last_error")
    CURRENT_STATE_FIELD_NUMBER: _ClassVar[int]
    SHOWFILE_APPLY_STATE_FIELD_NUMBER: _ClassVar[int]
    CURRENT_SCENE_FIELD_NUMBER: _ClassVar[int]
    LAST_CYCLE_TIME_FIELD_NUMBER: _ClassVar[int]
    LAST_ERROR_FIELD_NUMBER: _ClassVar[int]
    current_state: RunMode
    showfile_apply_state: _FilterMode_pb2.ShowFileApplyState
    current_scene: int
    last_cycle_time: int
    last_error: str
    def __init__(self, current_state: _Optional[_Union[RunMode, str]] = ..., showfile_apply_state: _Optional[_Union[_FilterMode_pb2.ShowFileApplyState, str]] = ..., current_scene: _Optional[int] = ..., last_cycle_time: _Optional[int] = ..., last_error: _Optional[str] = ...) -> None: ...

class long_log_update(_message.Message):
    __slots__ = ("level", "time_stamp", "what")
    LEVEL_FIELD_NUMBER: _ClassVar[int]
    TIME_STAMP_FIELD_NUMBER: _ClassVar[int]
    WHAT_FIELD_NUMBER: _ClassVar[int]
    level: LogLevel
    time_stamp: int
    what: str
    def __init__(self, level: _Optional[_Union[LogLevel, str]] = ..., time_stamp: _Optional[int] = ..., what: _Optional[str] = ...) -> None: ...
