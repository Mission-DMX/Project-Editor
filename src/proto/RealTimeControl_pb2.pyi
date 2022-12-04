import UniverseControl_pb2 as _UniverseControl_pb2
import DirectMode_pb2 as _DirectMode_pb2
import FilterMode_pb2 as _FilterMode_pb2
import Console_pb2 as _Console_pb2
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

from UniverseControl_pb2 import Universe
from UniverseControl_pb2 import universes_list
from UniverseControl_pb2 import request_universe_list
from UniverseControl_pb2 import delete_universe
from DirectMode_pb2 import dmx_output
from DirectMode_pb2 import request_dmx_data
from FilterMode_pb2 import enter_scene
from FilterMode_pb2 import load_show_file
from FilterMode_pb2 import update_parameter
from FilterMode_pb2 import ShowFileApplyState
from Console_pb2 import button_state_change
from Console_pb2 import fader_position
from Console_pb2 import rotary_encoder_change
from Console_pb2 import ButtonState
BS_ACTIVE: _Console_pb2.ButtonState
BS_BUTTON_PRESSED: _Console_pb2.ButtonState
BS_BUTTON_RELEASED: _Console_pb2.ButtonState
BS_SET_LED_BLINKING: _Console_pb2.ButtonState
BS_SET_LED_NOT_ACTIVE: _Console_pb2.ButtonState
DESCRIPTOR: _descriptor.FileDescriptor
RM_DIRECT: RunMode
RM_FILTER: RunMode
RM_STOP: RunMode
SFAS_ERROR_SHOW_RUNNING: _FilterMode_pb2.ShowFileApplyState
SFAS_INVALID: _FilterMode_pb2.ShowFileApplyState
SFAS_NO_SHOW_ERROR: _FilterMode_pb2.ShowFileApplyState
SFAS_SHOW_ACTIVE: _FilterMode_pb2.ShowFileApplyState
SFAS_SHOW_LOADING: _FilterMode_pb2.ShowFileApplyState
SFAS_SHOW_UPDATING: _FilterMode_pb2.ShowFileApplyState

class current_state(_message.Message):
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

class update_state(_message.Message):
    __slots__ = ["new_state"]
    NEW_STATE_FIELD_NUMBER: _ClassVar[int]
    new_state: RunMode
    def __init__(self, new_state: _Optional[_Union[RunMode, str]] = ...) -> None: ...

class RunMode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []
