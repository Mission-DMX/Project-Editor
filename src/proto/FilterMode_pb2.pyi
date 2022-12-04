from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor
SFAS_ERROR_SHOW_RUNNING: ShowFileApplyState
SFAS_INVALID: ShowFileApplyState
SFAS_NO_SHOW_ERROR: ShowFileApplyState
SFAS_SHOW_ACTIVE: ShowFileApplyState
SFAS_SHOW_LOADING: ShowFileApplyState
SFAS_SHOW_UPDATING: ShowFileApplyState

class enter_scene(_message.Message):
    __slots__ = ["scene_id"]
    SCENE_ID_FIELD_NUMBER: _ClassVar[int]
    scene_id: int
    def __init__(self, scene_id: _Optional[int] = ...) -> None: ...

class load_show_file(_message.Message):
    __slots__ = ["goto_default_scene", "show_data"]
    GOTO_DEFAULT_SCENE_FIELD_NUMBER: _ClassVar[int]
    SHOW_DATA_FIELD_NUMBER: _ClassVar[int]
    goto_default_scene: bool
    show_data: str
    def __init__(self, show_data: _Optional[str] = ..., goto_default_scene: bool = ...) -> None: ...

class update_parameter(_message.Message):
    __slots__ = ["filter_id", "parameter_key", "parameter_value"]
    FILTER_ID_FIELD_NUMBER: _ClassVar[int]
    PARAMETER_KEY_FIELD_NUMBER: _ClassVar[int]
    PARAMETER_VALUE_FIELD_NUMBER: _ClassVar[int]
    filter_id: str
    parameter_key: str
    parameter_value: str
    def __init__(self, filter_id: _Optional[str] = ..., parameter_key: _Optional[str] = ..., parameter_value: _Optional[str] = ...) -> None: ...

class ShowFileApplyState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []
