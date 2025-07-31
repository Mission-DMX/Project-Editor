import proto.UniverseControl_pb2 as _UniverseControl_pb2
import proto.DirectMode_pb2 as _DirectMode_pb2
import proto.FilterMode_pb2 as _FilterMode_pb2
import proto.Console_pb2 as _Console_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union


BS_ACTIVE: _Console_pb2.ButtonState
BS_BUTTON_PRESSED: _Console_pb2.ButtonState
BS_BUTTON_RELEASED: _Console_pb2.ButtonState
BS_SET_LED_BLINKING: _Console_pb2.ButtonState
BS_SET_LED_NOT_ACTIVE: _Console_pb2.ButtonState
BTN_ALT: _Console_pb2.ButtonCode
BTN_AUDIOINST: _Console_pb2.ButtonCode
BTN_AUDIOTRACKS: _Console_pb2.ButtonCode
BTN_AUX: _Console_pb2.ButtonCode
BTN_BEATS_OOPS: _Console_pb2.ButtonCode
BTN_BUSSES: _Console_pb2.ButtonCode
BTN_CANCEL_CANCEL: _Console_pb2.ButtonCode
BTN_CH1_ENCODER_ROTARYMODE: _Console_pb2.ButtonCode
BTN_CH1_MUTE_BLACK: _Console_pb2.ButtonCode
BTN_CH1_REC_READY: _Console_pb2.ButtonCode
BTN_CH1_SELECT_SELECT: _Console_pb2.ButtonCode
BTN_CH1_SOLO_FLASH: _Console_pb2.ButtonCode
BTN_CH2_ENCODER_ROTARYMODE: _Console_pb2.ButtonCode
BTN_CH2_MUTE_BLACK: _Console_pb2.ButtonCode
BTN_CH2_REC_READY: _Console_pb2.ButtonCode
BTN_CH2_SELECT_SELECT: _Console_pb2.ButtonCode
BTN_CH2_SOLO_FLASH: _Console_pb2.ButtonCode
BTN_CH3_ENCODER_ROTARYMODE: _Console_pb2.ButtonCode
BTN_CH3_MUTE_BLACK: _Console_pb2.ButtonCode
BTN_CH3_REC_READY: _Console_pb2.ButtonCode
BTN_CH3_SELECT_SELECT: _Console_pb2.ButtonCode
BTN_CH3_SOLO_FLASH: _Console_pb2.ButtonCode
BTN_CH4_ENCODER_ROTARYMODE: _Console_pb2.ButtonCode
BTN_CH4_MUTE_BLACK: _Console_pb2.ButtonCode
BTN_CH4_REC_READY: _Console_pb2.ButtonCode
BTN_CH4_SELECT_SELECT: _Console_pb2.ButtonCode
BTN_CH4_SOLO_FLASH: _Console_pb2.ButtonCode
BTN_CH5_ENCODER_ROTARYMODE: _Console_pb2.ButtonCode
BTN_CH5_MUTE_BLACK: _Console_pb2.ButtonCode
BTN_CH5_REC_READY: _Console_pb2.ButtonCode
BTN_CH5_SELECT_SELECT: _Console_pb2.ButtonCode
BTN_CH5_SOLO_FLASH: _Console_pb2.ButtonCode
BTN_CH6_ENCODER_ROTARYMODE: _Console_pb2.ButtonCode
BTN_CH6_MUTE_BLACK: _Console_pb2.ButtonCode
BTN_CH6_REC_READY: _Console_pb2.ButtonCode
BTN_CH6_SELECT_SELECT: _Console_pb2.ButtonCode
BTN_CH6_SOLO_FLASH: _Console_pb2.ButtonCode
BTN_CH7_ENCODER_ROTARYMODE: _Console_pb2.ButtonCode
BTN_CH7_MUTE_BLACK: _Console_pb2.ButtonCode
BTN_CH7_REC_READY: _Console_pb2.ButtonCode
BTN_CH7_SELECT_SELECT: _Console_pb2.ButtonCode
BTN_CH7_SOLO_FLASH: _Console_pb2.ButtonCode
BTN_CH8_ENCODER_ROTARYMODE: _Console_pb2.ButtonCode
BTN_CH8_MUTE_BLACK: _Console_pb2.ButtonCode
BTN_CH8_REC_READY: _Console_pb2.ButtonCode
BTN_CH8_SELECT_SELECT: _Console_pb2.ButtonCode
BTN_CH8_SOLO_FLASH: _Console_pb2.ButtonCode
BTN_CHNEXT_UNIVERSENEXT: _Console_pb2.ButtonCode
BTN_CHPREV_UNIVERSEPREV: _Console_pb2.ButtonCode
BTN_CLICK_IMAGE: _Console_pb2.ButtonCode
BTN_CONTROL: _Console_pb2.ButtonCode
BTN_CROSSENTER: _Console_pb2.ButtonCode
BTN_CYCLE_SHUTTER: _Console_pb2.ButtonCode
BTN_DOWN_DOWN: _Console_pb2.ButtonCode
BTN_DROP_COLOR: _Console_pb2.ButtonCode
BTN_ENTER_ENTER: _Console_pb2.ButtonCode
BTN_EQ_SHOWUI: _Console_pb2.ButtonCode
BTN_F1_F1: _Console_pb2.ButtonCode
BTN_F2_F2: _Console_pb2.ButtonCode
BTN_F3_F3: _Console_pb2.ButtonCode
BTN_F4_F4: _Console_pb2.ButtonCode
BTN_F5_F5: _Console_pb2.ButtonCode
BTN_F6_F6: _Console_pb2.ButtonCode
BTN_F7_F7: _Console_pb2.ButtonCode
BTN_F8_F8: _Console_pb2.ButtonCode
BTN_FADERBANKNEXT_FADERBANKNEXT: _Console_pb2.ButtonCode
BTN_FADERBANKPREV_FADERBANKPREV: _Console_pb2.ButtonCode
BTN_FF_NEXTCUE: _Console_pb2.ButtonCode
BTN_FLIP_MAINDARK: _Console_pb2.ButtonCode
BTN_GLOBALVIEW_COMMITRDY: _Console_pb2.ButtonCode
BTN_GROUP: _Console_pb2.ButtonCode
BTN_INPUTS_EVENTS: _Console_pb2.ButtonCode
BTN_INST_DEBUG: _Console_pb2.ButtonCode
BTN_LATCH: _Console_pb2.ButtonCode
BTN_LEFT_LEFT: _Console_pb2.ButtonCode
BTN_MARKER_GOBO: _Console_pb2.ButtonCode
BTN_MIDITRACKS_FIND: _Console_pb2.ButtonCode
BTN_NAMEVALUE_COMMITSHOW: _Console_pb2.ButtonCode
BTN_NUDGE_STROBO: _Console_pb2.ButtonCode
BTN_OPTION: _Console_pb2.ButtonCode
BTN_OUTPUTS: _Console_pb2.ButtonCode
BTN_PAN_EDITSHOW: _Console_pb2.ButtonCode
BTN_PLAY_RUNCUE: _Console_pb2.ButtonCode
BTN_PLUGIN_PATCH: _Console_pb2.ButtonCode
BTN_READOFF_GOTO: _Console_pb2.ButtonCode
BTN_REC_RECFRAME: _Console_pb2.ButtonCode
BTN_REPLACE_TEMPERATURE: _Console_pb2.ButtonCode
BTN_REV_LASTCUE: _Console_pb2.ButtonCode
BTN_RIGHT_RIGHT: _Console_pb2.ButtonCode
BTN_SAVE_SAVE: _Console_pb2.ButtonCode
BTN_SCRUB_JOGWHEELMODESWITCH: _Console_pb2.ButtonCode
BTN_SEND_VISUALIZER: _Console_pb2.ButtonCode
BTN_SHIFT: _Console_pb2.ButtonCode
BTN_SOLO_SPEED: _Console_pb2.ButtonCode
BTN_STOP_STOPCUE: _Console_pb2.ButtonCode
BTN_TOUCH: _Console_pb2.ButtonCode
BTN_TRACK_CONSOLE: _Console_pb2.ButtonCode
BTN_TRIM: _Console_pb2.ButtonCode
BTN_UNDO_UNDO: _Console_pb2.ButtonCode
BTN_UP_UP: _Console_pb2.ButtonCode
BTN_USER: _Console_pb2.ButtonCode
BTN_WRITE_MOVEWINDOW: _Console_pb2.ButtonCode
DESCRIPTOR: _descriptor.FileDescriptor
FADERTOUCH_CH1: _Console_pb2.ButtonCode
FADERTOUCH_CH2: _Console_pb2.ButtonCode
FADERTOUCH_CH3: _Console_pb2.ButtonCode
FADERTOUCH_CH4: _Console_pb2.ButtonCode
FADERTOUCH_CH5: _Console_pb2.ButtonCode
FADERTOUCH_CH6: _Console_pb2.ButtonCode
FADERTOUCH_CH7: _Console_pb2.ButtonCode
FADERTOUCH_CH8: _Console_pb2.ButtonCode
FADERTOUCH_MAIN: _Console_pb2.ButtonCode
LL_DEBUG: LogLevel
LL_ERROR: LogLevel
LL_INFO: LogLevel
LL_WARNING: LogLevel
RM_DIRECT: RunMode
RM_FILTER: RunMode
RM_STOP: RunMode
SFAS_ERROR_SHOW_RUNNING: _FilterMode_pb2.ShowFileApplyState
SFAS_INVALID: _FilterMode_pb2.ShowFileApplyState
SFAS_NO_SHOW_ERROR: _FilterMode_pb2.ShowFileApplyState
SFAS_SHOW_ACTIVE: _FilterMode_pb2.ShowFileApplyState
SFAS_SHOW_LOADING: _FilterMode_pb2.ShowFileApplyState
SFAS_SHOW_UPDATING: _FilterMode_pb2.ShowFileApplyState
black: _Console_pb2.lcd_color
blue: _Console_pb2.lcd_color
cyan: _Console_pb2.lcd_color
green: _Console_pb2.lcd_color
magenta: _Console_pb2.lcd_color
red: _Console_pb2.lcd_color
white: _Console_pb2.lcd_color
yellow: _Console_pb2.lcd_color

class current_state_update(_message.Message):
    __slots__ = ["current_scene", "current_state", "last_cycle_time", "last_error", "showfile_apply_state"]
    CURRENT_SCENE_FIELD_NUMBER: _ClassVar[int]
    CURRENT_STATE_FIELD_NUMBER: _ClassVar[int]
    LAST_CYCLE_TIME_FIELD_NUMBER: _ClassVar[int]
    LAST_ERROR_FIELD_NUMBER: _ClassVar[int]
    SHOWFILE_APPLY_STATE_FIELD_NUMBER: _ClassVar[int]
    current_scene: int
    current_state: RunMode
    last_cycle_time: int
    last_error: str
    showfile_apply_state: _FilterMode_pb2.ShowFileApplyState
    def __init__(self, current_state: _Optional[_Union[RunMode, str]] = ..., showfile_apply_state: _Optional[_Union[_FilterMode_pb2.ShowFileApplyState, str]] = ..., current_scene: _Optional[int] = ..., last_cycle_time: _Optional[int] = ..., last_error: _Optional[str] = ...) -> None: ...

class long_log_update(_message.Message):
    __slots__ = ["level", "time_stamp", "what"]
    LEVEL_FIELD_NUMBER: _ClassVar[int]
    TIME_STAMP_FIELD_NUMBER: _ClassVar[int]
    WHAT_FIELD_NUMBER: _ClassVar[int]
    level: LogLevel
    time_stamp: int
    what: str
    def __init__(self, level: _Optional[_Union[LogLevel, str]] = ..., time_stamp: _Optional[int] = ..., what: _Optional[str] = ...) -> None: ...

class state_list(_message.Message):
    __slots__ = ["specific_states", "unspecific_states"]
    class UnspecificStatesEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    class kvs(_message.Message):
        __slots__ = ["k", "scene_id", "v"]
        K_FIELD_NUMBER: _ClassVar[int]
        SCENE_ID_FIELD_NUMBER: _ClassVar[int]
        V_FIELD_NUMBER: _ClassVar[int]
        k: str
        scene_id: int
        v: str
        def __init__(self, k: _Optional[str] = ..., v: _Optional[str] = ..., scene_id: _Optional[int] = ...) -> None: ...
    SPECIFIC_STATES_FIELD_NUMBER: _ClassVar[int]
    UNSPECIFIC_STATES_FIELD_NUMBER: _ClassVar[int]
    specific_states: _containers.RepeatedCompositeFieldContainer[state_list.kvs]
    unspecific_states: _containers.ScalarMap[str, str]
    def __init__(self, unspecific_states: _Optional[_Mapping[str, str]] = ..., specific_states: _Optional[_Iterable[_Union[state_list.kvs, _Mapping]]] = ...) -> None: ...

class update_state(_message.Message):
    __slots__ = ["new_state"]
    NEW_STATE_FIELD_NUMBER: _ClassVar[int]
    new_state: RunMode
    def __init__(self, new_state: _Optional[_Union[RunMode, str]] = ...) -> None: ...

class RunMode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []

class LogLevel(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []
